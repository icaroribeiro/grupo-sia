import uuid
from langchain_core.messages import HumanMessage
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.language_models import BaseChatModel
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import functools
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import ToolNode


class DataReportingWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        async_query_sql_database_tools: list[BaseTool],
    ):
        self.name = "data_reporting_team"
        self.chat_model = chat_model
        self.data_reporting_agent_tools = async_query_sql_database_tools
        # self.supervisor = functools.partial(
        #     self.agent_node,
        #     name="supervisor",
        #     prompt=(
        #         """
        #         ROLE:
        #         - You're a supervisor coordinating a Data Analysis Agent.
        #         GOAL:
        #         - Manage the workflow by assigning tasks to the Data Analysis Agent and finalizing the process.
        #         INSTRUCTIONS:
        #         - If the input is a new task (e.g., the first message or a HumanMessage), append a HumanMessage with the task description prefixed by 'Task for data_reporting_agent: ' and route to the Data Analysis Agent.
        #         - If the Data Analysis Agent has provided analysis results (in an AIMessage, typically after tool execution), summarize the results and output them as the final answer.
        #         - DO NOT perform analysis yourself; only assign tasks and summarize results.
        #         CRITICAL RULES:
        #         - Assign work to the Data Analysis Agent one task at a time.
        #         - Complete the task when the Data Analysis Agent provides the final result.
        #         """
        #     ),
        #     llm_with_tools=self.chat_model,  # No tools for supervisor
        # )
        self.__graph = self.__build_graph()

    @staticmethod
    def call_agent(
        state: MessagesState,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ):
        logger.info(f"Calling {name} agent...")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        agent_chain = prompt_template | llm_with_tools
        result = agent_chain.invoke(state["messages"])
        return {"messages": state["messages"] + [result]}

    @staticmethod
    def route_agent(
        state: MessagesState,
        name: str,
    ) -> str:
        logger.info(f"Route from {name} agent...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "tools"
        else:
            routes_to = END
        logger.info(f"To {routes_to}...")
        return routes_to

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)

        builder.add_node(
            "data_reporting_agent",
            functools.partial(
                self.call_agent,
                name="data_reporting_agent",
                prompt=(
                    """
                    ROLE:
                    - You're a data reporting agent.
                    GOAL:
                    - Your sole purpose is to analyze data by executing SQL queries in database.
                    - DO NOT perform any other tasks.
                    CRITICAL RULES:
                    - ALWAYS interpret the user's question or task description to identify the data analysis task.
                    - If a specified table (e.g., 'invoices') does not exist, check for similar table names (e.g., 'invoice', 'Invoices', 'INVOICE') using case-insensitive or partial matching.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    self.data_reporting_agent_tools
                ),
            ),
        )
        builder.add_node("tools", ToolNode(tools=self.data_reporting_agent_tools))

        builder.add_edge(START, "data_reporting_agent")
        builder.add_edge("tools", "data_reporting_agent")
        builder.add_conditional_edges(
            "data_reporting_agent",
            functools.partial(self.route_agent, name="data_reporting_agent"),
            {
                "tools": "tools",
                END: END,
            },
        )

        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    async def run(self, input_message: str) -> MessagesState:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

        async for chunk in self.__graph.astream(
            input_state,
            subgraphs=True,
            config={"configurable": {"thread_id": thread_id}},
        ):
            self._pretty_print_messages(chunk, last_message=True)
        result = chunk[1]["data_reporting_agent"]["messages"]

        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")

        return {"messages": result}
