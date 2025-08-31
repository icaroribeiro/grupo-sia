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
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage  # noqa: F401
from langgraph.prebuilt import ToolNode


class DataReportingWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        async_query_sql_database_tools: list[BaseTool],
    ):
        self.name = "data_reporting_team"
        self.chat_model = chat_model
        self.data_analysis_agent_tools = async_query_sql_database_tools
        # self.delegate_to_data_analysis_agent = DataReportingHandoffTool(
        #     agent_name="data_analyst_agent",
        # )
        self.__graph = self.__build_graph()

    @staticmethod
    def call_persona(
        state: MessagesState,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ):
        logger.info(f"Calling {name} persona...")
        messages = state["messages"]
        logger.info(f"Messages: {messages}")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        agent_chain = prompt_template | llm_with_tools
        result = agent_chain.invoke(messages)
        return {"messages": messages + [result]}

    @staticmethod
    def route_supervisor(
        state: MessagesState,
        name: str,
    ) -> str:
        logger.info(f"Route from {name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if (
            isinstance(last_message, AIMessage)
            and "data analysis agent" in last_message.content.lower()
        ):
            routes_to = "data_analysis_agent"
        # if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        #     routes_to = "supervisor_tools"
        else:
            routes_to = END
        logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def route_supervisor_tools(
        state: MessagesState,
        name: str,
    ) -> str:
        logger.info(f"Route from {name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if isinstance(last_message, ToolMessage):
            if "transfer_to_data_analyst_agent" in last_message.content.lower():
                state["messages"] = state["messages"] + [
                    HumanMessage(
                        content="What is the invoice with the highest total value?"
                    )
                ]
                routes_to = "data_analysis_agent"
            else:
                routes_to = END
        else:
            routes_to = END
        logger.info(f"To {routes_to}...")
        return routes_to

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
            routes_to = "supervisor"
        logger.info(f"To {routes_to}...")
        return routes_to

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)

        builder.add_node(
            "supervisor",
            functools.partial(
                self.call_persona,
                name="supervisor",
                prompt=(
                    """
                    ROLE:
                    - You're a supervisor.
                    GOAL:
                    - Your sole purpose is to manage one agent:
                        - A Data Analysis Agent: Assign tasks related to data analysis to this agent.
                    INSTRUCTIONS:
                    - Based on the conversation history, decide the next step.
                    - DO NOT do any work yourself.
                    CRITICAL RULES:
                    - ALWAYS assign work to one agent at a time.
                    - DO NOT call agents in parallel.
                    """
                ),
                llm_with_tools=self.chat_model,
                # llm_with_tools=self.chat_model.bind_tools(
                #     tools=[self.delegate_to_data_analysis_agent]
                # ),
            ),
        )
        # builder.add_node(
        #     "supervisor_tools", ToolNode(tools=[self.delegate_to_data_analysis_agent])
        # )

        builder.add_node(
            "data_analysis_agent",
            functools.partial(
                self.call_persona,
                name="data_analysis_agent",
                prompt=(
                    """
                    ROLE:
                    - You're a data analysis agent.
                    GOAL:
                    - Your sole purpose is to analyze data by executing SQL queries in database.
                    - DO NOT perform any other tasks.
                    CRITICAL RULES:
                    - ALWAYS interpret the user's question or task description to identify the data analysis task.
                    - If a specified table (e.g., 'invoices') does not exist, check for similar table names (e.g., 'invoice', 'Invoices', 'INVOICE') using case-insensitive or partial matching.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    self.data_analysis_agent_tools
                ),
            ),
        )
        builder.add_node("tools", ToolNode(tools=self.data_analysis_agent_tools))

        builder.add_edge(START, "supervisor")
        builder.add_edge("tools", "data_analysis_agent")
        # builder.add_edge("supervisor_tools", "supervisor")
        builder.add_conditional_edges(
            "supervisor",
            functools.partial(self.route_supervisor, name="supervisor"),
            {"data_analysis_agent": "data_analysis_agent", END: END},
            # {"supervisor_tools": "supervisor_tools", END: END},
        )
        # builder.add_conditional_edges(
        #     "supervisor_tools",
        #     functools.partial(self.route_supervisor_tools, name="supervisor_tools"),
        #     {"data_analysis_agent": "data_analysis_agent", END: END},
        # )
        builder.add_conditional_edges(
            "data_analysis_agent",
            functools.partial(self.route_agent, name="data_analysis_agent"),
            {
                "tools": "tools",
                "supervisor": "supervisor",
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
        result = chunk[1]["supervisor"]["messages"]

        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")

        return {"messages": result}
