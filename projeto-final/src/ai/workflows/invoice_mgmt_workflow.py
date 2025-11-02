import functools
import json
from typing import Any, Dict

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool, ToolException
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.ai.agents.csv_mapping_agent import (
    CSVMappingAgent,
)
from src.ai.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.ai.agents.insert_records_agent import (
    InsertRecordsAgent,
)
from src.ai.agents.supervisor_agent import (
    SupervisorAgent,
)
from src.ai.agents.unzip_file_agent import (
    UnzipFileAgent,
)
from src.ai.models.invoice_mgmt_state_graph_model import (
    InvoiceMgmtStateGraphModel,
)
from src.ai.models.invoice_mgmt_state_model import (
    InvoiceMgmtStateModel,
)
from src.ai.tools.generate_bar_plot_tool import (
    GenerateBarPlotTool,
)
from src.ai.tools.generate_distribution_plot_tool import (
    GenerateDistributionPlotTool,
)
from src.ai.tools.get_detailed_table_schemas_tool import (
    GetDetailedTableSchemasTool,
)
from src.ai.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.ai.tools.invoice_mgmt_handoff_tool import (
    InvoiceMgmtHandoffTool,
)
from src.ai.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.ai.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.ai.workflows.base_workflow import (
    BaseWorkflow,
)
from src.core.logging import logger


class InvoiceMgmtWorkflow(BaseWorkflow):
    def __init__(
        self,
        unzip_file_agent: UnzipFileAgent,
        csv_mapping_agent: CSVMappingAgent,
        insert_records_agent: InsertRecordsAgent,
        data_analysis_agent: DataAnalysisAgent,
        supervisor_agent: SupervisorAgent,
        unzip_zip_file_tool: UnzipZipFileTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_records_into_database_tool: InsertRecordsIntoDatabaseTool,
        async_sql_database_tools: list[BaseTool],
        get_detailed_table_schemas_tool: GetDetailedTableSchemasTool,
        generate_bar_plot_tool: GenerateBarPlotTool,
        generate_distribution_plot_tool: GenerateDistributionPlotTool,
        delegate_to_unzip_file_agent_tool: InvoiceMgmtHandoffTool,
        delegate_to_csv_mapping_agent_tool: InvoiceMgmtHandoffTool,
        delegate_to_insert_records_agent_tool: InvoiceMgmtHandoffTool,
        delegate_to_data_analysis_agent_tool: InvoiceMgmtHandoffTool,
    ):
        super().__init__()
        self.name = "invoice_mgmt_workflow"
        self.unzip_file_agent = unzip_file_agent
        self.csv_mapping_agent = csv_mapping_agent
        self.insert_records_agent = insert_records_agent
        self.data_analysis_agent = data_analysis_agent
        self.supervisor_agent = supervisor_agent
        self.unzip_zip_file_tool = unzip_zip_file_tool
        self.map_csvs_to_ingestion_args_tool = map_csvs_to_ingestion_args_tool
        self.insert_records_into_database_tool = insert_records_into_database_tool
        self.data_analysis_tools = async_sql_database_tools + [
            get_detailed_table_schemas_tool,
            generate_bar_plot_tool,
            generate_distribution_plot_tool,
        ]
        self.delegate_to_unzip_file_agent_tool = delegate_to_unzip_file_agent_tool
        self.delegate_to_csv_mapping_agent_tool = delegate_to_csv_mapping_agent_tool
        self.delegate_to_insert_records_agent_tool = (
            delegate_to_insert_records_agent_tool
        )
        self.delegate_to_data_analysis_agent_tool = delegate_to_data_analysis_agent_tool

    def _build_workflow(self) -> InvoiceMgmtStateGraphModel:
        builder = StateGraph(state_schema=InvoiceMgmtStateModel)
        self.__add_nodes(builder)
        self.__add_edges(builder)
        self.__add_conditional_edges(builder)
        return InvoiceMgmtStateGraphModel(name=self.name, graph=builder)

    def __add_nodes(self, builder: StateGraph) -> None:
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
            node=self.data_analysis_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.data_analysis_agent,
                llm_with_tools=self.data_analysis_agent.chat_model.bind_tools(
                    tools=self.data_analysis_tools,
                ),
            ),
        )
        builder.add_node(
            node=self.supervisor_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.supervisor_agent,
                llm_with_tools=self.supervisor_agent.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_unzip_file_agent_tool,
                        self.delegate_to_csv_mapping_agent_tool,
                        self.delegate_to_insert_records_agent_tool,
                        self.delegate_to_data_analysis_agent_tool,
                    ]
                ),
            ),
        )

        builder.add_node(
            node="tools",
            action=ToolNode(
                tools=[self.unzip_zip_file_tool, self.map_csvs_to_ingestion_args_tool]
                + self.data_analysis_tools
            ),
        )
        builder.add_node(
            node="insert_records_agent_tools", action=self.insert_records_agent_tools
        )
        builder.add_node(node="tool_output_node", action=self.tool_output_node)
        builder.add_node(
            node="handoff_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_unzip_file_agent_tool,
                    self.delegate_to_csv_mapping_agent_tool,
                    self.delegate_to_insert_records_agent_tool,
                    self.delegate_to_data_analysis_agent_tool,
                ]
            ),
        )
        builder.add_node(
            node="handoff_node",
            action=functools.partial(self.handoff_node, agent=self.supervisor_agent),
        )
        builder.add_node(node="final_response", action=self.prepare_final_response)

    def __add_edges(self, builder: StateGraph) -> None:
        builder.add_edge(start_key=START, end_key=self.supervisor_agent.name)
        builder.add_edge(start_key="tools", end_key="tool_output_node")
        builder.add_edge(
            start_key="insert_records_agent_tools",
            end_key="tool_output_node",
        )
        builder.add_edge(start_key="handoff_tools", end_key="handoff_node")
        builder.add_edge(start_key="final_response", end_key=END)

    def __add_conditional_edges(self, builder: StateGraph) -> None:
        builder.add_conditional_edges(
            source="tool_output_node",
            path=functools.partial(
                self.route_tool_output,
                routes_to_by_tool_name={
                    "unzip_zip_file_tool": self.unzip_file_agent.name,
                    "map_csvs_to_ingestion_args_tool": self.csv_mapping_agent.name,
                    "insert_records_into_database_tool": self.insert_records_agent.name,
                    **{
                        tool.name: self.data_analysis_agent.name
                        for tool in self.data_analysis_tools
                    },
                },
            ),
            path_map={
                self.unzip_file_agent.name: self.unzip_file_agent.name,
                self.csv_mapping_agent.name: self.csv_mapping_agent.name,
                self.insert_records_agent.name: self.insert_records_agent.name,
                self.data_analysis_agent.name: self.data_analysis_agent.name,
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.unzip_file_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.unzip_file_agent,
                routes_to=self.supervisor_agent.name,
                routes_to_by_tool_name={
                    self.unzip_zip_file_tool.name: "tools",
                },
            ),
            path_map={
                "tools": "tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.csv_mapping_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.csv_mapping_agent,
                routes_to=self.supervisor_agent.name,
                routes_to_by_tool_name={
                    self.map_csvs_to_ingestion_args_tool.name: "tools",
                },
            ),
            path_map={
                "tools": "tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.insert_records_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.insert_records_agent,
                routes_to=self.supervisor_agent.name,
                routes_to_by_tool_name={
                    self.insert_records_into_database_tool.name: "insert_records_agent_tools",
                },
            ),
            path_map={
                "insert_records_agent_tools": "insert_records_agent_tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.data_analysis_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.data_analysis_agent,
                routes_to=self.supervisor_agent.name,
                routes_to_by_tool_name={
                    tool.name: "tools" for tool in self.data_analysis_tools
                },
            ),
            path_map={
                "tools": "tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.supervisor_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.supervisor_agent,
                routes_to="final_response",
                routes_to_by_tool_name={
                    self.delegate_to_unzip_file_agent_tool.name: "handoff_tools",
                    self.delegate_to_csv_mapping_agent_tool.name: "handoff_tools",
                    self.delegate_to_insert_records_agent_tool.name: "handoff_tools",
                    self.delegate_to_data_analysis_agent_tool.name: "handoff_tools",
                },
            ),
            path_map={
                "handoff_tools": "handoff_tools",
                "final_response": "final_response",
            },
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                self.unzip_file_agent.name: self.unzip_file_agent.name,
                self.csv_mapping_agent.name: self.csv_mapping_agent.name,
                self.insert_records_agent.name: self.insert_records_agent.name,
                self.data_analysis_agent.name: self.data_analysis_agent.name,
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )

    async def insert_records_agent_tools(
        self, state: InvoiceMgmtStateModel
    ) -> Dict[str, Any]:
        logger.info("Calling insert_records_agent_tools node...")
        messages = state["messages"]
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        tool_results = []

        tool_calls = last_message.tool_calls
        if not tool_calls:
            logger.warning(
                "No ingestion arguments found in state. Skipping database insertion."
            )
            return state

        tool_name = self.insert_records_into_database_tool.name
        tool_instance = self.insert_records_into_database_tool
        tool_call = tool_calls[0]
        tool_call_id = tool_call["id"]

        ingestion_args_list = state.get("ingestion_args_list")
        if not ingestion_args_list:
            logger.warning(
                "No ingestion arguments found in state. Skipping database insertion."
            )
            return {
                "messages": messages
                + [
                    ToolMessage(
                        content="Database insertion was skipped because no CSV ingestion arguments were provided.",
                        tool_call_id=tool_call_id,
                        name=self.insert_records_into_database_tool.name,
                    )
                ]
            }

        tool_args = {"ingestion_args_list": ingestion_args_list}

        try:
            tool_result = await tool_instance.ainvoke(
                {
                    "name": tool_name,
                    "args": tool_args,
                    "id": tool_call_id,
                    "type": "tool_call",
                }
            )

            content = tool_result.content
            artifact = tool_result.artifact

            tool_results.append(
                ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id,
                    name=tool_name,
                    artifact=artifact,
                )
            )

        except ToolException as error:
            logger.error(f"Error executing tool {tool_name}: {error}")
            tool_results.append(
                ToolMessage(
                    content=f"Tool execution failed: {error}",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )
        except Exception as error:
            logger.error(f"Unexpected error executing tool {tool_name}: {error}")
            tool_results.append(
                ToolMessage(
                    content=f"Tool execution failed due to unexpected error: {error}",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

        new_messages = messages + tool_results

        return {
            "messages": new_messages,
            "ingestion_args_list": None,
        }

    @staticmethod
    def tool_output_node(state: InvoiceMgmtStateModel) -> dict[str, Any]:
        logger.info("Calling tool_output...")
        last_message = state["messages"][-1]
        logger.info(f"Last message: {last_message}")

        ingestion_args_list = state.get("ingestion_args_list", [])
        if (
            isinstance(last_message, ToolMessage)
            and last_message.name == "map_csvs_to_ingestion_args_tool"
        ):
            if last_message.artifact:
                ingestion_args_list = last_message.artifact
                logger.info(
                    f"Successfully extracted {len(ingestion_args_list)} ingestion arguments from tool artifact."
                )
            else:
                logger.warning("ToolMessage found, but artifact was empty or None.")
                ingestion_args_list = []

        chart_data = state.get("chart_data")
        if isinstance(last_message, ToolMessage) and last_message.name in [
            "generate_bar_plot_tool",
            "generate_distribution_plot_tool",
        ]:
            if last_message.artifact and isinstance(last_message.artifact, dict):
                chart_data = {
                    "chart": last_message.artifact,
                    "description": last_message.content,
                }

                logger.info("Successfully extracted chart data from tool artifact.")
            else:
                logger.error(
                    f"The {last_message.name} returned no valid chart artifact (expected dict)."
                )

        return {
            "messages": state["messages"],
            "ingestion_args_list": ingestion_args_list,
            "chart_data": chart_data,
        }

    def route_tool_output(
        self,
        state: InvoiceMgmtStateModel,
        routes_to_by_tool_name: dict[str, str] | None,
    ) -> str:
        logger.info("Routing from tool_output...")
        last_tool_message = state["messages"][-1]
        tool_name = last_tool_message.name
        routes_to: str = ""
        if routes_to_by_tool_name:
            routes_to = routes_to_by_tool_name.get(
                tool_name, self.supervisor_agent.name
            )
        else:
            routes_to = self.supervisor_agent.name
        logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def prepare_final_response(state: InvoiceMgmtStateModel) -> dict:
        logger.info("Preparing final response...")
        chart_data = state.get("chart_data")
        messages = state["messages"]

        last_message = messages[-1]
        if chart_data and last_message:
            final_content = {
                "text": last_message.content,
                "description": chart_data.get("description"),
                "chart": chart_data.get("chart"),
            }
            final_message = AIMessage(content=json.dumps(final_content))

            return {
                "messages": messages[:-1] + [final_message],
                "chart_data": None,
            }

        return {"messages": messages}
