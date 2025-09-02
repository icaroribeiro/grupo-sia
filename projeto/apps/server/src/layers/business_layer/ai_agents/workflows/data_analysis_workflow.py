import re
import uuid
from langchain_core.messages import HumanMessage
from src.layers.business_layer.ai_agents.models.data_analysis_state_model import (
    DataAnalysisStateModel,
)
from src.layers.business_layer.ai_agents.models.top_level_state_model import (
    TopLevelStateModel,
)
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import functools
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import ToolNode


class DataAnalysisWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        async_query_sql_database_tools: list[BaseTool],
    ):
        self.name = "data_analysis_team"
        self.chat_model = chat_model
        self.data_analysis_agent_tools = async_query_sql_database_tools
        self.delegate_to_data_analysis_agent = DataAnalysisHandoffTool(
            agent_name="data_analysis_agent",
        )
        self.delegate_to_data_formatting_agent = DataAnalysisHandoffTool(
            agent_name="data_formatting_agent",
        )
        self.__graph = self.__build_graph()

    @staticmethod
    def call_persona(
        state: DataAnalysisStateModel,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> DataAnalysisStateModel:
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

    @staticmethod
    def route_supervisor(
        state: DataAnalysisStateModel,
        name: str,
    ) -> str:
        logger.info(f"Routing from {name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "supervisor_tools"
        else:
            routes_to = END
        logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def route_agent(
        state: DataAnalysisStateModel,
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
    def handoff_node(state: DataAnalysisStateModel) -> DataAnalysisStateModel:
        logger.info("Calling handoff_node...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message.content: {last_message.content}")
        pattern = r"transfer_to_agent=(\w+)::task=(.+)"
        match = re.search(pattern, last_message.content)
        if match:
            agent_name = match.group(1)
            task_description = match.group(2)
            logger.info(f"Parsed agent: {agent_name}, task= {task_description}")
            new_task_message = HumanMessage(content=task_description)
            return {
                "messages": state["messages"] + [new_task_message],
                "next_agent": agent_name,
            }
        logger.warning("No valid agent transfer found in handoff_node")
        return {"messages": state["messages"], "next_agent": "supervisor"}

    @staticmethod
    def route_handoff(state: DataAnalysisStateModel) -> str:
        logger.info("Routing from handoff_node...")
        # logger.info(f"state: {state}")
        next_agent = state.get("next_agent", "supervisor")
        logger.info(f"To {next_agent}...")
        return next_agent

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=DataAnalysisStateModel)

        builder.add_node(
            node="supervisor",
            action=functools.partial(
                self.call_persona,
                name="supervisor",
                prompt=(
                    """
                    ROLE:
                    - You're a supervisor.
                    GOAL:
                    - Your sole purpose is to manage two agents:
                        - A Data Analysis Agent: Assign tasks related to data analysis to this agent.
                        - A Data Formatting Agent: Assign tasks related to data formatting to this agent.
                    INSTRUCTIONS:
                    - Based on the conversation history, decide the next step.
                    - DO NOT do any work yourself.
                    CRITICAL RULES:
                    - ALWAYS assign work to one agent at time.
                    - DO NOT call agents in parallel.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_data_analysis_agent,
                        self.delegate_to_data_formatting_agent,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="data_analysis_agent",
            action=functools.partial(
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
            node="data_formatting_agent",
            action=functools.partial(
                self.call_persona,
                name="data_formatting_agent",
                prompt=(
                    """
                    ROLE:
                    - You're a data formatting agent.
                    GOAL:
                    - Your sole purpose is to format data.
                    - DO NOT perform any other tasks.
                    CRITICAL RULES:
                    - ALWAYS check for any formatting instructions before responding.
                    - Interpret the analysis result and if it's already in a suitable format, you can return it without any changes.
                    """
                ),
                llm_with_tools=self.chat_model,
            ),
        )
        builder.add_node(
            node="tools", action=ToolNode(tools=self.data_analysis_agent_tools)
        )
        builder.add_node(
            node="supervisor_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_data_analysis_agent,
                    self.delegate_to_data_formatting_agent,
                ]
            ),
        )
        builder.add_node("handoff_node", self.handoff_node)

        builder.add_edge(start_key=START, end_key="supervisor")
        builder.add_edge(start_key="tools", end_key="data_analysis_agent")
        builder.add_edge(start_key="supervisor_tools", end_key="handoff_node")
        builder.add_conditional_edges(
            source="supervisor",
            path=functools.partial(self.route_supervisor, name="supervisor"),
            path_map={"supervisor_tools": "supervisor_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                "data_analysis_agent": "data_analysis_agent",
                "data_formatting_agent": "data_formatting_agent",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            source="data_analysis_agent",
            path=functools.partial(self.route_agent, name="data_analysis_agent"),
            path_map={
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            source="data_formatting_agent",
            path=functools.partial(self.route_agent, name="data_formatting_agent"),
            path_map={
                "supervisor": "supervisor",
            },
        )

        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    # async def run(self, input_message: str) -> DataAnalysisStateModel:
    # logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
    # input_messages = [HumanMessage(content=input_message)]
    # thread_id = str(uuid.uuid4())
    # input_state = {"messages": input_messages}
    async def run(self, state: TopLevelStateModel) -> DataAnalysisStateModel:
        logger.info(f"Starting {self.name} with input: '{state['messages'][:100]}...'")
        thread_id = str(uuid.uuid4())
        input_state = state

        async for chunk in self.__graph.astream(
            input_state,
            subgraphs=True,
            config={"configurable": {"thread_id": thread_id}},
        ):
            self._pretty_print_messages(chunk, last_message=True)
        result = chunk[1]["supervisor"]["messages"]
        logger.info(f"{self.name} final result: complete.")
        return {"messages": result}
