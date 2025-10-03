import functools
import re

from langchain_core.messages import ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.layers.business_layer.ai_agents.agents.csv_mapping_agent import CSVMappingAgent
from src.layers.business_layer.ai_agents.agents.data_ingestion_supervisor_agent import (
    DataIngestionSupervisorAgent,
)
from src.layers.business_layer.ai_agents.agents.insert_records_agent import (
    InsertRecordsAgent,
)
from src.layers.business_layer.ai_agents.agents.unzip_file_agent import UnzipFileAgent
from src.layers.business_layer.ai_agents.models.data_ingestion_state_graph_model import (
    DataIngestionStateGraphModel,
)
from src.layers.business_layer.ai_agents.models.data_ingestion_state_model import (
    DataIngestionStateModel,
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
from src.layers.business_layer.ai_agents.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.logging import logger


class DataIngestionWorkflow(BaseWorkflow):
    def __init__(
        self,
        unzip_zip_file_tool: UnzipZipFileTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_records_into_database_tool: InsertRecordsIntoDatabaseTool,
        unzip_file_agent: UnzipFileAgent,
        csv_mapping_agent: CSVMappingAgent,
        insert_records_agent: InsertRecordsAgent,
        data_ingestion_supervisor_agent: DataIngestionSupervisorAgent,
        delegate_to_unzip_file_agent_tool: DataIngestionHandoffTool,
        delegate_to_csv_mapping_agent_tool: DataIngestionHandoffTool,
        delegate_to_insert_records_agent_tool: DataIngestionHandoffTool,
    ):
        self.name = "data_ingestion_workflow"
        self.unzip_zip_file_tool = unzip_zip_file_tool
        self.map_csvs_to_ingestion_args_tool = map_csvs_to_ingestion_args_tool
        self.insert_records_into_database_tool = insert_records_into_database_tool
        self.unzip_file_agent = unzip_file_agent
        self.csv_mapping_agent = csv_mapping_agent
        self.insert_records_agent = insert_records_agent
        self.data_ingestion_supervisor_agent = data_ingestion_supervisor_agent
        self.delegate_to_unzip_file_agent_tool = delegate_to_unzip_file_agent_tool
        self.delegate_to_csv_mapping_agent_tool = delegate_to_csv_mapping_agent_tool
        self.delegate_to_insert_records_agent_tool = (
            delegate_to_insert_records_agent_tool
        )

    def _build_workflow(self) -> DataIngestionStateGraphModel:
        builder = StateGraph(state_schema=DataIngestionStateModel)
        self.__add_nodes(builder)
        self.__add_edges(builder)
        self.__add_conditional_edges(builder)
        return DataIngestionStateGraphModel(name=self.name, graph=builder)

    def __add_nodes(self, builder: StateGraph) -> None:
        builder.add_node(
            node="tools",
            action=ToolNode(
                tools=[
                    self.unzip_zip_file_tool,
                    self.map_csvs_to_ingestion_args_tool,
                    self.insert_records_agent,
                ]
            ),
        )
        builder.add_node("insert_records_tool_node", self.insert_records_tool_node)
        builder.add_node("tool_output_node", self.tool_output_node)
        builder.add_node(
            node=self.unzip_file_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.unzip_file_agent,
                llm_with_tools=self.unzip_file_agent.chat_model.bind_tools(
                    tools=[
                        self.unzip_zip_file_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node=self.csv_mapping_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.csv_mapping_agent,
                llm_with_tools=self.csv_mapping_agent.chat_model.bind_tools(
                    tools=[
                        self.map_csvs_to_ingestion_args_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node=self.insert_records_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.insert_records_agent,
                llm_with_tools=self.insert_records_agent.chat_model.bind_tools(
                    tools=[
                        self.insert_records_into_database_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node=self.data_ingestion_supervisor_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.data_ingestion_supervisor_agent,
                llm_with_tools=self.data_ingestion_supervisor_agent.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_unzip_file_agent_tool,
                        self.delegate_to_csv_mapping_agent_tool,
                        self.delegate_to_insert_records_agent_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="handoff_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_unzip_file_agent,
                    self.delegate_to_csv_mapping_agent,
                    self.delegate_to_insert_records_agent,
                ]
            ),
        )
        builder.add_node(
            node="handoff_node",
            action=functools.partial(
                self.handoff_node, agent=self.data_ingestion_supervisor_agent
            ),
        )

    def __add_edges(self, builder: StateGraph) -> None:
        builder.add_edge(
            start_key=START, end_key=self.data_ingestion_supervisor_agent.name
        )
        builder.add_edge(start_key="tools", end_key="tool_output_node")
        # builder.add_edge(start_key="tool_output_node", end_key="supervisor")
        builder.add_edge(start_key="handoff_tools", end_key="handoff_node")

    def __add_conditional_edges(self, builder: StateGraph) -> None:
        builder.add_conditional_edges(
            source=self.unzip_file_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.unzip_file_agent.name,
                routes_to=self.data_ingestion_supervisor_agent.name,
            ),
            path_map={
                "tools": "tools",
                self.data_ingestion_supervisor_agent.name: self.data_ingestion_supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.csv_mapping_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.csv_mapping_agent.name,
                routes_to=self.data_ingestion_supervisor_agent.name,
            ),
            path_map={
                "tools": "tools",
                self.data_ingestion_supervisor_agent.name: self.data_ingestion_supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.insert_records_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.insert_records_agent.name,
                routes_to=self.data_ingestion_supervisor_agent.name,
            ),
            path_map={
                "tools": "tools",
                "insert_records_tool_node": "insert_records_tool_node",
                self.data_ingestion_supervisor_agent.name: self.data_ingestion_supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source="tool_output_node",
            path=functools.partial(
                self.route_tool_output,
                routes_to_by_tool_name={
                    "unzip_zip_file_tool": self.data_ingestion_supervisor_agent.name,
                    "map_csvs_to_ingestion_args_tool": self.data_ingestion_supervisor_agent.name,
                    "insert_records_into_database_tool": END,
                },
                fallback=self.data_ingestion_supervisor_agent.name,
            ),
            path_map={
                self.data_ingestion_supervisor_agent.name: self.data_ingestion_supervisor_agent.name,
                END: END,
            },
        )
        builder.add_conditional_edges(
            source=self.data_ingestion_supervisor_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.data_ingestion_supervisor_agent.name,
                routes_to=END,
                is_handoff=True,
            ),
            path_map={"handoff_tools": "handoff_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                self.unzip_file_agent.name: self.unzip_file_agent.name,
                self.csv_mapping_agent.name: self.csv_mapping_agent.name,
                self.insert_records_agent.name: self.insert_records_agent.name,
                self.data_ingestion_supervisor_agent.name: self.data_ingestion_supervisor_agent.name,
            },
        )

    async def insert_records_tool_node(self, state: DataIngestionStateModel):
        logger.info("Calling insert_records_tool_node node...")
        messages = state["messages"]
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        tool_results = []
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_calls = last_message.tool_calls
            if not tool_calls:
                logger.error("No ingestion args found in state. Skipping insertion.")
                return state
            tool_call = tool_calls[0]
            tool_call_id = tool_call["id"]
            ingestion_args_list = state.get("ingestion_args_list", [])
            logger.info(f"ingestion_args_list: {ingestion_args_list}")
            if ingestion_args_list:
                tool_message = await self.insert_records_into_database_tool._arun(
                    ingestion_args_list=ingestion_args_list,
                    tool_call_id=tool_call_id,
                )
                tool_results.append(tool_message)
            else:
                logger.error("No ingestion args found in state. Skipping insertion.")
                tool_results.append(
                    ToolMessage(
                        content="Tool execution failed because no ingestion args found in state",
                        tool_call_id=tool_call_id,
                    )
                )
        new_state = {"messages": messages + tool_results}
        return new_state

    @staticmethod
    def tool_output_node(state: DataIngestionStateModel):
        logger.info("Calling tool output node...")
        # messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        last_message = state["messages"][-1]
        logger.info(f"Last message: {last_message}")
        ingestion_args_list: list[str] = []
        if "ingestion_args_list" in last_message.content:
            pattern = r"ingestion_args_list:(.+)"
            match = re.search(pattern, last_message.content)
            if match:
                ingestion_args_str = match.group(1)
                try:
                    ingestion_args_list = eval(ingestion_args_str)
                except Exception as e:
                    logger.error(f"Error parsing ingestion args: {e}")
        logger.info(f"ingestion_args_list: {ingestion_args_list}")
        return {"messages": state["messages"], "ingestion_args_str": ingestion_args_str}

    def route_tool_output(
        self,
        state: DataIngestionStateModel,
        routes_to_by_tool_name: dict[str, str] | None,
        fallback: str,
    ) -> str:
        logger.info("Routing from tool_output...")
        last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        routes_to: str = fallback
        if routes_to_by_tool_name:
            routes_to = routes_to_by_tool_name.get(last_message.name, fallback)
        logger.info(f"To {routes_to}...")
        return routes_to
