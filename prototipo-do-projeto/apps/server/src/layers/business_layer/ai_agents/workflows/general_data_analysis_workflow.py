import uuid
from typing import Annotated, Sequence, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from src.layers.core_logic_layer.logging import logger


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str


class Agent(BaseModel):
    name: str
    tools: list[BaseTool] | None = None


class GeneralDataAnalysisWorkflow:
    def __init__(self, llm: BaseChatModel, async_sql_database_tools: list[BaseTool]):
        self.name = "GeneralDataAnalysisWorkflow"
        self.llm = llm
        self.supervisor = Agent(name="supervisor")
        self.assistant_1 = Agent(name="assistant_1", tools=async_sql_database_tools)
        self.assistant_names = [self.assistant_1.name]
        self.__graph = self._build_graph()

    def __call_supervisor(self, state: WorkflowState):
        logger.info(f"Calling {self.supervisor.name} (Supervisor Agent)...")
        messages = state["messages"]

        # if (
        #     messages
        #     and isinstance(messages[-1], AIMessage)
        #     and messages[-1].content
        # ):
        #     # If the last message is a content-ful AIMessage (not a tool call),
        #     # we assume this is the final answer and route to FINISH.
        #     if not (
        #         hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls
        #     ):
        #         logger.info("Supervisor found final answer. Routing to: FINISH")
        #         return {"next": "FINISH"}

        assistant_names = self.assistant_names
        assistant_names_str = ", ".join(assistant_names)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a team supervisor routing tasks to assistants. 
                    Your primary goal is to ensure the user's request is fully completed.
                    
                    Current available assistants: [{assistant_names_str}].
                    
                    **Here are your CRITICAL instructions:**
                    1.  Analyze the user request and the entire conversation history.
                    2.  Your task is to determine the NEXT step.
                    
                    **Routing Logic:**
                    - If the **last message in the conversation** is a final, conclusive answer to the user's original request, route to FINISH. A final answer will be a human-readable message, not a tool-calling message or a tool output.
                    - If the task requires a new action or a different assistant to proceed, route to the appropriate assistant (e.g., `assistant_1`).
                    
                    Respond in the following JSON format:
                    ```json
                        {{"next": "<next_node>"}}
                    ```
                    where <next_node> is the node to route to (e.g., {entry_node} 
                    or {finish_node}).
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            assistant_names_str=assistant_names_str,
            finish_node="FINISH",
            entry_node=self.assistant_names[0],
        )
        chain = prompt | self.llm | JsonOutputParser()
        response = chain.invoke({"messages": messages})
        logger.info(f"{self.supervisor.name} routing to: {response['next']}")
        return {"next": response["next"]}

    def __call_assistant_1(self, state: WorkflowState):
        logger.info(f"Calling {self.assistant_1.name} (Data Analysis Agent)...")
        messages = state["messages"]
        logger.info(f"messages: {messages}")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a data analysis specialist.
                    You must use the provided tools to interact with the SQL database to answer the user's question. 
                    **Immediately call the tool to get the necessary information.**
                    Do not try to answer without using a tool first.
                    Once the tool has been used and you have the final answer, provide it directly without calling any more tools.
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        llm_with_tools = self.llm.bind_tools(self.assistant_1.tools)
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})

        # The agent's response is the key to routing.
        # We don't need to return 'next' here, the conditional edge will handle it.
        # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
        return {"messages": [response]}

    def __route_from_supervisor(self, state: WorkflowState):
        logger.info(f"Routing from {self.supervisor.name}...")
        next_node = state["next"]
        logger.info(f"Routing decision: '{next_node}'")
        return next_node

    def __route_from_assistant_1(self, state: WorkflowState):
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

    def _build_graph(self) -> StateGraph:
        # Build the graph
        workflow = StateGraph(state_schema=WorkflowState)

        workflow.add_node(self.supervisor.name, self.__call_supervisor)
        workflow.add_node(self.assistant_1.name, self.__call_assistant_1)
        workflow.add_node(
            node="tools",
            action=ToolNode(self.assistant_1.tools),
        )

        workflow.set_entry_point(self.supervisor.name)

        workflow.add_conditional_edges(
            self.supervisor.name,
            self.__route_from_supervisor,
            {
                self.assistant_1.name: self.assistant_1.name,
                "FINISH": END,
            },
        )

        workflow.add_conditional_edges(
            self.assistant_1.name,
            self.__route_from_assistant_1,
            {"tools": "tools", self.supervisor.name: self.supervisor.name},
        )

        workflow.add_edge("tools", self.assistant_1.name)

        # Compile the graph
        logger.info(f"Graph Name: {self.name}")
        graph = workflow.compile(checkpointer=MemorySaver())
        logger.info("Graph with all assistants compiled successfully!")
        logger.info(graph.get_graph(xray=True).draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(self, input_message: str) -> dict:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

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
