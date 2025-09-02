import functools
import re
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from src.layers.business_layer.ai_agents.models.data_ingestion_state_model import (
    DataIngestionStateModel,
)
from src.layers.business_layer.ai_agents.models.top_level_state_model import (
    TopLevelStateModel,
)
from src.layers.business_layer.ai_agents.tools.data_ingestion_handoff_tool import (
    DataIngestionHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.logging import logger
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import ToolNode


class DataIngestionWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_records_into_database_tool: InsertRecordsIntoDatabaseTool,
    ):
        self.name = "data_ingestion_team"
        self.chat_model = chat_model
        self.unzip_files_from_zip_archive_tool = unzip_files_from_zip_archive_tool
        self.map_csvs_to_ingestion_args_tool = map_csvs_to_ingestion_args_tool
        self.insert_records_into_database_tool = insert_records_into_database_tool
        self.delegate_to_data_gathering_agent = DataIngestionHandoffTool(
            agent_name="data_gathering_agent",
        )
        self.delegate_to_data_wrangling_agent = DataIngestionHandoffTool(
            agent_name="data_wrangling_agent",
        )
        self.delegate_to_data_inserting_agent = DataIngestionHandoffTool(
            agent_name="data_inserting_agent"
        )
        self.__graph = self.__build_graph()

    @staticmethod
    def call_persona(
        state: DataIngestionStateModel,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> DataIngestionStateModel:
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
        state: DataIngestionStateModel,
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
        state: DataIngestionStateModel,
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
    def handoff_node(state: DataIngestionStateModel) -> DataIngestionStateModel:
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
    def route_handoff(state: DataIngestionStateModel) -> str:
        logger.info("Routing from handoff_node...")
        # logger.info(f"state: {state}")
        next_agent = state.get("next_agent", "supervisor")
        logger.info(f"To {next_agent}...")
        return next_agent

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=DataIngestionStateModel)

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
                    - Your sole purpose is to manage two agent:
                        - A Data Gathering Agent: Assign tasks related to data gathering to this agent.
                        - A Data Wrangling Agent: Assign tasks related to data wrangling to this agent.
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
                        self.delegate_to_data_gathering_agent,
                        self.delegate_to_data_wrangling_agent,
                        self.delegate_to_data_inserting_agent,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="data_gathering_agent",
            action=functools.partial(
                self.call_persona,
                name="data_gathering_agent",
                prompt=(
                    """
                    ROLE:
                    - You're a data gathering agent.
                    GOAL:
                    - Your sole purpose is to unzip files from ZIP archive.
                    - DO NOT perform any other tasks.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[self.unzip_files_from_zip_archive_tool]
                ),
            ),
        )
        builder.add_node(
            node="data_wrangling_agent",
            action=functools.partial(
                self.call_persona,
                name="data_wrangling_agent",
                prompt=(
                    """
                    ROLE:
                    - You're a data wrangling agent.
                    GOAL:
                     Your sole purpose is to map csv files into ingestion arguments.
                    - DO NOT perform any other tasks.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[self.map_csvs_to_ingestion_args_tool]
                ),
            ),
        )
        builder.add_node(
            node="tools",
            action=ToolNode(
                tools=[
                    self.unzip_files_from_zip_archive_tool,
                    self.map_csvs_to_ingestion_args_tool,
                    self.insert_records_into_database_tool,
                ]
            ),
        )
        builder.add_node(
            node="supervisor_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_data_gathering_agent,
                    self.delegate_to_data_wrangling_agent,
                    self.delegate_to_data_inserting_agent,
                ]
            ),
        )
        builder.add_node("handoff_node", self.handoff_node)

        builder.add_edge(start_key=START, end_key="supervisor")
        builder.add_edge(start_key="tools", end_key="data_gathering_agent")
        builder.add_edge(start_key="tools", end_key="data_wrangling_agent")
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
                "data_gathering_agent": "data_gathering_agent",
                "data_wrangling_agent": "data_wrangling_agent",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            source="data_gathering_agent",
            path=functools.partial(self.route_agent, name="data_gathering_agent"),
            path_map={
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            source="data_wrangling_agent",
            path=functools.partial(self.route_agent, name="data_wrangling_agent"),
            path_map={
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )

        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    # async def run(self, input_message: str) -> DataIngestionStateModel:
    # logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
    # input_messages = [HumanMessage(content=input_message)]
    # thread_id = str(uuid.uuid4())
    # input_state = {"messages": input_messages}
    async def run(self, state: TopLevelStateModel) -> DataIngestionStateModel:
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
