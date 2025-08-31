import re
import uuid
from langchain_core.messages import HumanMessage
from src.layers.business_layer.ai_agents.tools.data_reporting_handoff_tool import (
    DataReportingHandoffTool,
)
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import functools
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage  # noqa: F401
from langgraph.prebuilt import ToolNode  # noqa: F401
from typing import TypedDict
from typing import Sequence

from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class NewStateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str


class DataReportingWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        async_query_sql_database_tools: list[BaseTool],
    ):
        self.name = "data_reporting_team"
        self.chat_model = chat_model
        self.data_analysis_agent_tools = async_query_sql_database_tools
        self.delegate_to_data_analysis_agent = DataReportingHandoffTool(
            agent_name="data_analysis_agent",
        )
        self.delegate_to_data_reporting_agent = DataReportingHandoffTool(
            agent_name="data_reporting_agent",
        )
        self.__graph = self.__build_graph()

    @staticmethod
    def call_persona(
        state: NewStateModel,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> NewStateModel:
        logger.info(f"Calling {name} persona...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        agent_chain = prompt_template | llm_with_tools
        result = agent_chain.invoke(messages)
        return {"messages": messages + [result]}

    # @staticmethod
    # def route_supervisor(
    #     state: NewStateModel,
    #     name: str,
    # ) -> str:
    #     logger.info(f"Routing from {name}...")
    #     last_message = state["messages"][-1]
    #     logger.info(f"Last_message: {last_message}")
    #     routes_to: str = ""
    #     # if (
    #     #     isinstance(last_message, AIMessage)
    #     #     and "data analysis agent" in last_message.content.lower()
    #     # ):
    #     #     routes_to = "data_analysis_agent"
    #     # if (
    #     #     isinstance(last_message, AIMessage)
    #     #     and "data reporting agent" in last_message.content.lower()
    #     # ):
    #     #     routes_to = "data_reporting_agent"
    #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
    #         routes_to = "supervisor_tools"
    #     else:
    #         routes_to = END
    #     logger.info(f"To {routes_to}...")
    #     return routes_to

    @staticmethod
    def route_supervisor(
        state: NewStateModel,
        name: str,
    ) -> str:
        logger.info(f"Routing from {name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message: {last_message}")
        # If the last message has tool calls, route to supervisor_tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("To supervisor_tools...")
            return "supervisor_tools"
        # If a ToolMessage for transfer_to_data_analyst_agent exists, but not for transfer_to_data_reporting_agent,
        # route to supervisor_tools to delegate to data_reporting_agent
        has_analysis_handoff = any(
            isinstance(m, ToolMessage) and m.name == "transfer_to_data_analyst_agent"
            for m in state["messages"]
        )
        has_reporting_handoff = any(
            isinstance(m, ToolMessage) and m.name == "transfer_to_data_reporting_agent"
            for m in state["messages"]
        )
        if has_analysis_handoff and not has_reporting_handoff:
            logger.info("To supervisor_tools for reporting handoff...")
            return "supervisor_tools"
        # If a ToolMessage for transfer_to_data_reporting_agent exists, end the workflow
        if has_reporting_handoff:
            logger.info("To END...")
            return END
        # Default to supervisor_tools for initial or continued processing
        logger.info("To supervisor_tools...")
        return "supervisor_tools"

    @staticmethod
    def route_agent(
        state: NewStateModel,
        name: str,
    ) -> str:
        logger.info(f"Routing from {name} agent...")
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "tools"
        else:
            routes_to = "supervisor"
        logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def handoff_node(state: NewStateModel) -> dict:
        logger.info("Calling handoff_node...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message.content: {last_message.content}")
        pattern = r"transfer_to_agent:(\w+)::task:(.+)"
        match = re.search(pattern, last_message.content)
        if match:
            agent_name = match.group(1)
            task_description = match.group(2)
            logger.info(f"Parsed agent: {agent_name}, task: {task_description}")
            new_task_message = HumanMessage(content=task_description)
            return {
                "messages": state["messages"] + [new_task_message],
                "next_agent": agent_name,
            }
        logger.warning("No valid agent transfer found in handoff_node")
        return {"messages": state["messages"], "next_agent": "supervisor"}

    @staticmethod
    def route_handoff(state: NewStateModel) -> str:
        logger.info("Routing from handoff_node...")
        # logger.info(f"state: {state}")
        next_agent = state.get("next_agent", "supervisor")
        logger.info(f"To {next_agent}...")
        return next_agent

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=NewStateModel)

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
                    - Your sole purpose is to manage two agents:
                        - A Data Analysis Agent: Assign tasks related to data analysis to this agent.
                        - A Data Reporting Agent: Assign tasks related to data reporting to this agent.
                    INSTRUCTIONS:
                    - DO NOT do any work yourself.
                    CRITICAL RULES:
                    - Delegate tasks sequentially: first to Data Analysis Agent, then to Data Reporting Agent.
                    - DO NOT call agents in parallel.
                    - DO NOT summarize or output a final result until the Data Reporting Agent provides the formatted report.
                    - If the Data Analysis Agent returns an error, propagate the error to the Data Reporting Agent for reporting.
                    """
                ),
                # llm_with_tools=self.chat_model,
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_data_analysis_agent,
                        self.delegate_to_data_reporting_agent,
                    ]
                ),
            ),
        )
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
        builder.add_node(
            "data_reporting_agent",
            functools.partial(
                self.call_persona,
                name="data_reporting_agent",
                prompt=(
                    """
                    ROLE:
                    - You're a data reporting agent.
                    GOAL:
                    - Your sole purpose is to report data.
                    - DO NOT perform any other tasks.
                    CRITICAL RULES:
                    - ALWAYS check for any formatting instructions before responding.
                    - ALWAYS interpret the response, and if it's already in a suitable format, you can return it without any changes.
                    """
                ),
                llm_with_tools=self.chat_model,
            ),
        )
        builder.add_node("tools", ToolNode(tools=self.data_analysis_agent_tools))
        builder.add_node(
            "supervisor_tools",
            ToolNode(
                tools=[
                    self.delegate_to_data_analysis_agent,
                    self.delegate_to_data_reporting_agent,
                ]
            ),
        )
        builder.add_node("handoff_node", self.handoff_node)

        builder.add_edge(START, "supervisor")
        builder.add_edge("tools", "data_analysis_agent")
        builder.add_edge("supervisor_tools", "handoff_node")
        # builder.add_edge("data_analysis_agent", "supervisor")
        # builder.add_edge("data_reporting_agent", "supervisor")
        # builder.add_edge("handoff_node", "data_analysis_agent")
        # builder.add_edge("handoff_node", "data_reporting_agent")
        builder.add_conditional_edges(
            "supervisor",
            functools.partial(self.route_supervisor, name="supervisor"),
            # {
            #     "data_analysis_agent": "data_analysis_agent",
            #     # "data_reporting_agent": "data_reporting_agent",
            #     END: END,
            # },
            {"supervisor_tools": "supervisor_tools", END: END},
        )
        builder.add_conditional_edges(
            "handoff_node",
            self.route_handoff,
            {
                "data_analysis_agent": "data_analysis_agent",
                "data_reporting_agent": "data_reporting_agent",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            "data_analysis_agent",
            functools.partial(self.route_agent, name="data_analysis_agent"),
            {
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            "data_reporting_agent",
            functools.partial(self.route_agent, name="data_reporting_agent"),
            {
                "supervisor": "supervisor",
            },
        )

        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    async def run(self, input_message: str) -> NewStateModel:
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
