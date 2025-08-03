from typing import Annotated, Sequence, TypedDict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.layers.core_logic_layer.logging import logger
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import uuid
from langgraph.graph import END
from langchain_core.messages import AIMessage, HumanMessage


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str


class GeneralDataAnalysisWorkflow:
    def __init__(self, llm: BaseChatModel, async_sql_database_tools: list[BaseTool]):
        self.llm = llm
        self.assistant_1_tools = async_sql_database_tools
        self.all_tools = self.assistant_1_tools
        self.name = "General Data Aalysis Workflow"
        self.__graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(state_schema=WorkflowState)

        def call_supervisor(state: WorkflowState):
            logger.info("---SUPERVISOR---")
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

            assistant_names = ["assistant_1"]
            assistant_names_str = ", ".join(assistant_names)
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a team supervisor routing tasks to assistants. 
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
                entry_node="assistant_1",
            )
            chain = prompt | self.llm | JsonOutputParser()
            response = chain.invoke({"messages": messages})
            logger.info(f"Supervisor routing to: {response['next']}")
            return {"next": response["next"]}

        def call_assistant_1(state: WorkflowState):
            logger.info("---ASSISTANT 1 (DATA ANALYSIS AGENT)---")
            messages = state["messages"]
            logger.info(f"messages: {messages}")
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a data analysis specialist. "
                        "You must use the provided tools to interact with the SQL database to answer the user's question. "
                        "**Immediately call the tool to get the necessary information.** "
                        "Do not try to answer without using a tool first. "
                        "Once the tool has been used and you have the final answer, provide it directly without calling any more tools.",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            llm_with_tools = self.llm.bind_tools(self.assistant_1_tools)
            chain = prompt | llm_with_tools
            response = chain.invoke({"messages": messages})

            # The agent's response is the key to routing.
            # We don't need to return 'next' here, the conditional edge will handle it.
            # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
            return {"messages": [response]}

        # Build the Graph
        workflow.add_node("supervisor", call_supervisor)
        workflow.add_node("assistant_1", call_assistant_1)
        workflow.add_node(
            node="tools",
            action=ToolNode(self.all_tools),
        )

        workflow.set_entry_point("supervisor")

        # Route from the supervisor
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state["next"],
            {
                "assistant_1": "assistant_1",
                "FINISH": END,
            },
        )

        # Route from assistant_1
        def route_from_assistant_1(state: WorkflowState):
            logger.info("--- ROUTING from assistant_1 ---")
            last_message = state["messages"][-1]
            logger.info(f"Last message content: {last_message.content}")
            logger.info(
                f"Tool calls found: {hasattr(last_message, 'tool_calls') and last_message.tool_calls}"
            )

            # FIX: Check for both tool_calls and final content.
            # If there are tool calls, go to the tools node.
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                logger.info("Routing decision: 'tools' (tool calls found)")
                return "tools"
            # If the LLM has provided a final answer, route back to the supervisor to finish.
            elif hasattr(last_message, "content") and last_message.content:
                logger.info("Routing decision: 'supervisor' (final content found)")
                return "supervisor"
            # Otherwise, something went wrong, and we should probably route back to the supervisor
            # or have a more robust error handling mechanism. For now, we'll route to supervisor.
            else:
                logger.warning(
                    "Routing decision: 'supervisor' (no tool calls or final content)"
                )
                return "supervisor"

        workflow.add_conditional_edges(
            "assistant_1",
            route_from_assistant_1,
            {"tools": "tools", "supervisor": "supervisor"},
        )

        # Route from tools
        workflow.add_edge("tools", "assistant_1")

        # Compile the graph
        graph = workflow.compile(checkpointer=MemorySaver())
        logger.info("✅ Graph with all assistants compiled successfully!")
        logger.info(f"Graph Name: {self.name}")
        logger.info(graph.get_graph(xray=True).draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(self, input_message: str) -> dict:
        logger.info(f"🚀 Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

        # Use a `stream` approach or simply `ainvoke` and let the graph run to END.
        result = await self.__graph.ainvoke(
            input_state,
            config={"configurable": {"thread_id": thread_id}},
        )

        logger.info("\n✅ GeneralDataAnalysisWorkflow Finished.")

        final_message = "Workflow complete."
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                final_message = msg.content
                break
        logger.info(f"Final Result: {final_message}")
        return result
