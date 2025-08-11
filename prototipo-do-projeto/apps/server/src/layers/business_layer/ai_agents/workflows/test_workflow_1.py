import json
import math
import random
import re
import uuid
from typing import Annotated, Any, Sequence, Type, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field
from langgraph.prebuilt import ToolNode
from src.layers.core_logic_layer.logging import logger
from langchain_core.messages import ToolMessage


class ToolOutput(BaseModel):
    message: str = ""
    result: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str
    sender: str
    format_instructions: str | None = None


class Agent(BaseModel):
    name: str
    tools: list[BaseTool] | None = None


class CreateRandomNumberTool(BaseTool):
    name: str = "create_random_number_tool"
    description: str = "Generates a random number between 1 and 100."

    def _run(self) -> ToolOutput:
        logger.info("Generating random number")
        result = random.randint(1, 100)
        logger.info(f"Generated random number: {result}")
        return ToolOutput(message="Success", result=result)

    async def _arun(self) -> ToolOutput:
        return self._run()


class IsPrimeNumberInput(BaseModel):
    num: int = Field(..., description="The number to check if it's prime or not.")


class IsPrimeNumberTool(BaseTool):
    name: str = "is_prime_number_tool"
    description: str = "Check if the number is prime or not."
    args_schema: Type[BaseModel] = IsPrimeNumberInput

    def _run(self, num: int) -> ToolOutput:
        if num <= 1:
            return ToolOutput(message="Success", result=False)

        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                return ToolOutput(message="Success", result=False)

        return ToolOutput(message="Success", result=True)

    async def _arun(self, num: int) -> str:
        return self._run(num)


class TestWorkflow1:
    def __init__(
        self,
        llm: BaseChatModel,
        create_random_number_tool: CreateRandomNumberTool,
        is_prime_number_tool: IsPrimeNumberTool,
    ):
        self.name = "test_workflow"
        self.llm = llm
        self.supervisor = Agent(name="supervisor")
        self.assistant_1 = Agent(name="assistant_1", tools=[create_random_number_tool])
        self.assistant_2 = Agent(name="assistant_2", tools=[is_prime_number_tool])
        self.assistant_names = [self.assistant_1.name, self.assistant_2.name]
        self.reporter = Agent(name="reporter")
        self.__graph = self._build_graph()

    def __call_supervisor(self, state: WorkflowState):
        logger.info(f"Calling {self.supervisor.name}...")
        messages = state["messages"]
        assistant_names = self.assistant_names
        assistant_names_str = ", ".join(assistant_names)

        # START OF CHANGE: Supervisor prompt updated to recognize the 'tool_output' key.
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a team supervisor routing tasks between the following assistants: 
                    {assistant_names_str}.
                    
                    **Routing Logic:**
                    - The conversation history contains messages. Look for the last message from an assistant.
                    - If the last message is a JSON object with a **'tool_output'** key, it means a tool has run.
                    - Analyze the **'tool_output'** to decide the next step.
                    - If the request is not yet complete, route to the appropriate assistant.
                    - Once the request is complete, route to the {reporter_name} to respond user request using format instructions
                    Respond with a JSON object with a single key 'next' mapping to one of [{assistant_names_str}, {reporter_name}, FINISH] as follows:
                    ```json
                        {{"next": "<next_node>"}}
                    ```
                    where <next_node> is the node to route to (e.g., {assistant_1_name}, {reporter_name} or FINISH).
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            assistant_names_str=assistant_names_str,
            reporter_name=self.reporter.name,
            assistant_1_name=self.assistant_1.name,
        )
        # END OF CHANGE

        chain = prompt | self.llm | JsonOutputParser()
        response = chain.invoke({"messages": messages})
        logger.info(f"{self.supervisor.name} routing to: {response['next']}")
        return {"next": response["next"]}

    def __call_assistant_1(self, state: WorkflowState):
        logger.info(f"Calling {self.assistant_1.name}...")
        messages = state["messages"]

        # START OF CHANGE: Find ToolMessage and create structured AIMessage
        last_tool_message = None
        for msg in reversed(messages):
            if (
                isinstance(msg, ToolMessage)
                and msg.name == self.assistant_1.tools[0].name
            ):
                last_tool_message = msg
                break

        if last_tool_message:
            logger.info("Found previous tool result. Creating structured AIMessage.")

            content_str = last_tool_message.content
            logger.info(f"content_str: {content_str}")

            # Define a regex pattern to capture the message and result values.
            # This pattern is more robust as it handles spaces inside the message string.
            pattern = r"message='(.*?)' result=(.*)"

            match = re.search(pattern, content_str)
            if match:
                # Extract the captured groups
                message_value = match.group(1)
                result_value_str = match.group(2)

                # --- START OF CHANGE ---
                # Check for boolean values first
                if result_value_str.lower() == "true":
                    result_value = True
                elif result_value_str.lower() == "false":
                    result_value = False
                else:
                    # Then try to convert to an integer
                    try:
                        result_value = int(result_value_str)
                    except (ValueError, TypeError):
                        result_value = None
                # --- END OF CHANGE ---
            else:
                # If the regex doesn't match, fall back to default values
                message_value = content_str
                result_value = None

            # Create a ToolOutput instance with the parsed values
            tool_output = ToolOutput(message=message_value, result=result_value)

            # Now, serialize the ToolOutput object to JSON
            structured_content = json.dumps(
                {"tool_output": tool_output.model_dump()}, indent=2
            )

            final_message = AIMessage(content=structured_content)
            return {"messages": [final_message], "sender": self.assistant_1.name}

        logger.info("No previous tool result found. Calling LLM to get tool call.")
        # END OF CHANGE

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are an expert in creating random numbers.
                    You have access to the following tools to perform your activities:
                    {tool_descriptions}

                    Your mission is to find the necessary input from the conversation history, choose the appropriate tool from your available set to process that input, and then stop.
                    The required input will be provided in a JSON object from a previous assistant. You must extract the value from the **'result'** field of the **'tool_output'** object. This value should be used as the primary input argument for the tool you select.
                    Your task is complete once you have called a tool and processed the input.
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            tool_descriptions="\n".join(
                [
                    f"- `{tool.name}`: {tool.description.strip()}"
                    for tool in self.assistant_1.tools
                ]
            )
        )
        llm_with_tools = self.llm.bind_tools(self.assistant_1.tools)
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})

        # Deduplicate tool calls before updating the state
        # This ensures that only unique tool calls (based on name and arguments) are
        # passed to the tools node.
        if hasattr(response, "tool_calls") and response.tool_calls:
            seen = set()
            unique_tool_calls = []
            for tool_call in response.tool_calls:
                tool_key = (tool_call["name"], str(tool_call["args"]))
                if tool_key not in seen:
                    seen.add(tool_key)
                    unique_tool_calls.append(tool_call)
            response.tool_calls = unique_tool_calls

        return {"messages": [response], "sender": self.assistant_1.name}

    def __call_assistant_2(self, state: WorkflowState):
        logger.info(f"Calling {self.assistant_2.name}...")
        messages = state["messages"]

        # START OF CHANGE: Find ToolMessage and create structured AIMessage for assistant_2
        last_tool_message = None
        for msg in reversed(messages):
            if (
                isinstance(msg, ToolMessage)
                and msg.name == self.assistant_2.tools[0].name
            ):
                last_tool_message = msg
                break

        if last_tool_message:
            logger.info("Found previous tool result. Creating structured AIMessage.")

            content_str = last_tool_message.content
            logger.info(f"content_str: {content_str}")
            # Define a regex pattern to capture the message and result values.
            # This pattern is more robust as it handles spaces inside the message string.
            pattern = r"message='(.*?)' result=(.*)"

            match = re.search(pattern, content_str)
            if match:
                # Extract the captured groups
                message_value = match.group(1)
                result_value_str = match.group(2)

                # --- START OF CHANGE ---
                # Check for boolean values first
                if result_value_str.lower() == "true":
                    result_value = True
                elif result_value_str.lower() == "false":
                    result_value = False
                else:
                    # Then try to convert to an integer
                    try:
                        result_value = int(result_value_str)
                    except (ValueError, TypeError):
                        result_value = None
                # --- END OF CHANGE ---
            else:
                # If the regex doesn't match, fall back to default values
                message_value = content_str
                result_value = None

            # Create a ToolOutput instance with the parsed values
            tool_output = ToolOutput(message=message_value, result=result_value)

            # Now, serialize the ToolOutput object to JSON
            structured_content = json.dumps(
                {"tool_output": tool_output.model_dump()}, indent=2
            )

            final_message = AIMessage(content=structured_content)
            return {"messages": [final_message], "sender": self.assistant_2.name}

        logger.info("No previous tool result found. Calling LLM to get tool call.")

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are an expert in checking if a number is prime.
                    You have access to the following tools to perform your activities:
                    {tool_descriptions}

                    Your mission is to find the necessary input from the conversation history, choose the appropriate tool from your available set to process that input, and then stop.
                    The required input will be provided in a JSON object from a previous assistant. You must extract the value from the **'result'** field of the **'tool_output'** object. This value should be used as the primary input argument for the tool you select.
                    Your task is complete once you have called a tool and processed the input.
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            tool_descriptions="\n".join(
                [
                    f"- `{tool.name}`: {tool.description.strip()}"
                    for tool in self.assistant_2.tools
                ]
            )
        )
        llm_with_tools = self.llm.bind_tools(self.assistant_2.tools)
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})

        # Deduplicate tool calls before updating the state
        # This ensures that only unique tool calls (based on name and arguments) are
        # passed to the tools node.
        if hasattr(response, "tool_calls") and response.tool_calls:
            seen = set()
            unique_tool_calls = []
            for tool_call in response.tool_calls:
                tool_key = (tool_call["name"], str(tool_call["args"]))
                if tool_key not in seen:
                    seen.add(tool_key)
                    unique_tool_calls.append(tool_call)
            response.tool_calls = unique_tool_calls

        return {"messages": [response], "sender": self.assistant_2.name}

    def __call_reporter(self, state: WorkflowState):
        logger.info(f"Calling {self.reporter.name}...")
        messages = state["messages"]

        logger.info(f"messages: {messages}")
        # Retrieve format instructions from the state, defaulting to an empty string
        format_instructions = state.get("format_instructions", "")
        logger.info(f"format_instructions: {format_instructions}")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a reporter.
                    Once you have the final answer, please provide it directly using the formatting rules if any.
                    \n\n{format_instructions}
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | self.llm
        response = chain.invoke(
            {"messages": messages, "format_instructions": format_instructions}
        )
        return {"messages": [response], "sender": self.reporter.name}

    def __route_from_supervisor(self, state: WorkflowState):
        logger.info(f"Routing from {self.supervisor.name}...")
        next_node = state["next"]
        logger.info(f"Routing decision: '{next_node}'")
        return next_node

    def __route_from_assistant(self, state: WorkflowState):
        logger.info(f"Routing from {self.assistant_1.name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last message content: {last_message.content}")
        logger.info(
            f"Tool calls found: {hasattr(last_message, 'tool_calls') and last_message.tool_calls}"
        )

        # If there are tool calls, go to the tools node.
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("Routing decision: 'tools' (tool calls found)")
            return "tools"
        # If the LLM has provided a final answer, route back to the supervisor to finish.
        elif hasattr(last_message, "content") and last_message.content:
            logger.info(
                f"Routing decision: '{self.supervisor.name}' (final content found)"
            )
            return self.supervisor.name
        # Otherwise, something went wrong, and we should probably route back to the supervisor
        # or have a more robust error handling mechanism. For now, we'll route to supervisor.
        else:
            logger.warning(
                f"Routing decision: '{self.supervisor.name}' (no tool calls or final content)"
            )
            return self.supervisor.name

    def __route_from_tools(self, state: WorkflowState):
        logger.info("Routing from tools back to...")
        next_node = state["sender"]
        logger.info(f"Routing decision: '{next_node}'")
        return next_node

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(state_schema=WorkflowState)

        workflow.add_node(self.supervisor.name, self.__call_supervisor)
        workflow.add_node(self.assistant_1.name, self.__call_assistant_1)
        workflow.add_node(self.assistant_2.name, self.__call_assistant_2)
        workflow.add_node(self.reporter.name, self.__call_reporter)
        workflow.add_node(
            node="tools",
            action=ToolNode(self.assistant_1.tools + self.assistant_2.tools),
        )

        workflow.set_entry_point(self.supervisor.name)

        routing_map = {name: name for name in self.assistant_names}
        routing_map[self.reporter.name] = self.reporter.name
        routing_map["FINISH"] = END
        workflow.add_conditional_edges(
            self.supervisor.name,
            self.__route_from_supervisor,
            routing_map,
        )

        workflow.add_conditional_edges(
            self.assistant_1.name,
            self.__route_from_assistant,
            {"tools": "tools", self.supervisor.name: self.supervisor.name},
        )
        workflow.add_conditional_edges(
            self.assistant_2.name,
            self.__route_from_assistant,
            {"tools": "tools", self.supervisor.name: self.supervisor.name},
        )

        tool_routing_map = {name: name for name in self.assistant_names}
        workflow.add_conditional_edges(
            "tools", self.__route_from_tools, tool_routing_map
        )

        graph = workflow.compile(checkpointer=MemorySaver())
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(graph.get_graph(xray=True).draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(
        self, input_message: str, format_instructions_str: str | None
    ) -> dict:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")

        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())

        input_state = {
            "messages": input_messages,
            "format_instructions": format_instructions_str,
        }

        result = await self.__graph.ainvoke(
            input_state,
            config={"configurable": {"thread_id": thread_id}},
        )

        final_message = f"{self.name} complete."
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                final_message = msg.content
                break
        logger.info(f"{self.name} final result: {final_message}")
        return result
