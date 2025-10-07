import functools
import json
import re

from langchain_core.tools import BaseTool
import pandas as pd
from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_experimental.tools import PythonAstREPLTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.agents.supervisor_agent import SupervisorAgent
from src.layers.business_layer.ai_agents.agents.unzip_file_agent import UnzipFileAgent
from src.layers.business_layer.ai_agents.models.data_analysis_state_graph_model import (
    DataAnalysisStateGraphModel,
)
from src.layers.business_layer.ai_agents.models.data_analysis_state_model import (
    DataAnalysisStateModel,
)
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.logging import logger


class DataAnalysisWorkflow(BaseWorkflow):
    def __init__(
        self,
        unzip_zip_file_tool: UnzipZipFileTool,
        unzip_file_agent: UnzipFileAgent,
        data_analysis_agent: DataAnalysisAgent,
        supervisor_agent: SupervisorAgent,
        delegate_to_unzip_file_agent_tool: DataAnalysisHandoffTool,
        delegate_to_data_analysis_agent_tool: DataAnalysisHandoffTool,
        eda_tools: list[BaseTool],
    ) -> None:
        super().__init__()
        self.name = "data_analysis_workflow"
        self.unzip_zip_file_tool = unzip_zip_file_tool
        self.unzip_file_agent = unzip_file_agent
        self.data_analysis_agent = data_analysis_agent
        self.supervisor_agent = supervisor_agent
        self.delegate_to_unzip_file_agent_tool = delegate_to_unzip_file_agent_tool
        self.delegate_to_data_analysis_agent_tool = delegate_to_data_analysis_agent_tool
        self.eda_tools = eda_tools

    def _build_workflow(self) -> DataAnalysisStateGraphModel:
        builder = StateGraph(state_schema=DataAnalysisStateModel)
        self.__add_nodes(builder)
        self.__add_edges(builder)
        self.__add_conditional_edges(builder)
        return DataAnalysisStateGraphModel(name=self.name, graph=builder)

    def __add_nodes(self, builder: StateGraph) -> None:
        builder.add_node(
            node="tools",
            action=ToolNode(tools=[self.unzip_zip_file_tool]),
        )
        builder.add_node(
            node="data_analysis_agent_tools",
            action=self.data_analysis_agent_tools,
        )
        builder.add_node("tool_output_node", self.tool_output_node)
        builder.add_node(
            node=self.unzip_file_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.unzip_file_agent,
                llm_with_tools=self.unzip_file_agent.chat_model.bind_tools(
                    tools=[self.unzip_zip_file_tool]
                ),
            ),
        )
        builder.add_node(
            node=self.data_analysis_agent.name,
            action=self.data_analysis_agent_node,
        )
        builder.add_node(
            node=self.supervisor_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.supervisor_agent,
                llm_with_tools=self.supervisor_agent.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_unzip_file_agent_tool,
                        self.delegate_to_data_analysis_agent_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="handoff_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_unzip_file_agent_tool,
                    self.delegate_to_data_analysis_agent_tool,
                ]
            ),
        )
        builder.add_node(
            node="handoff_node",
            action=functools.partial(self.handoff_node, agent=self.supervisor_agent),
        )
        builder.add_node(node="cleanup_node", action=self.cleanup_node)

    def __add_edges(self, builder: StateGraph) -> None:
        builder.add_edge(start_key=START, end_key=self.supervisor_agent.name)
        builder.add_edge(start_key="tools", end_key="tool_output_node")
        builder.add_edge(
            start_key="data_analysis_agent_tools",
            end_key="tool_output_node",
        )
        builder.add_edge(start_key="handoff_tools", end_key="handoff_node")
        builder.add_edge(start_key="cleanup_node", end_key=END)

    def __add_conditional_edges(self, builder: StateGraph) -> None:
        # builder.add_conditional_edges(
        #     source="tool_output_node",
        #     path=self.route_tool_output,
        #     path_map={
        #         self.supervisor_agent.name: self.supervisor_agent.name,
        #         "cleanup_and_end": "cleanup_node",
        #     },
        # )
        builder.add_conditional_edges(
            source="tool_output_node",
            path=self.route_tool_output,
            path_map={
                self.unzip_file_agent.name: self.unzip_file_agent.name,
                self.data_analysis_agent.name: self.data_analysis_agent.name,
                self.supervisor_agent.name: self.supervisor_agent.name,
                "cleanup_and_end": "cleanup_node",
            },
        )
        builder.add_conditional_edges(
            source=self.unzip_file_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.unzip_file_agent,
                routes_to=self.supervisor_agent.name,
                routes_to_by_tool_name={},
                is_handoff=False,
            ),
            path_map={
                "tools": "tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        # builder.add_conditional_edges(
        #     source=self.data_analysis_agent.name,
        #     path=functools.partial(
        #         self.route_tools,
        #         agent=self.data_analysis_agent,
        #         routes_to=self.supervisor_agent.name,
        #         routes_to_by_tool_name={
        #             "python_repl_ast": "data_analysis_agent_tools",
        #             "generate_distribution_tool": "data_analysis_agent_tools",
        #         },
        #         is_handoff=False,
        #     ),
        #     path_map={
        #         "data_analysis_agent_tools": "data_analysis_agent_tools",
        #         self.supervisor_agent.name: self.supervisor_agent.name,
        #     },
        # )
        builder.add_conditional_edges(
            source=self.data_analysis_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.data_analysis_agent,
                routes_to=self.supervisor_agent.name,
                routes_to_by_tool_name={
                    "python_repl_ast": "data_analysis_agent_tools",
                    "generate_distribution_tool": "data_analysis_agent_tools",
                },
                is_handoff=False,
            ),
            path_map={
                "data_analysis_agent_tools": "data_analysis_agent_tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
                END: END,
            },
        )
        builder.add_conditional_edges(
            source=self.supervisor_agent.name,
            path=functools.partial(
                self.route_tools,
                agent=self.supervisor_agent,
                routes_to=END,
                routes_to_by_tool_name={},
                is_handoff=True,
            ),
            path_map={"handoff_tools": "handoff_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                self.unzip_file_agent.name: self.unzip_file_agent.name,
                self.data_analysis_agent.name: self.data_analysis_agent.name,
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )

    def data_analysis_agent_tools(
        self, state: DataAnalysisStateModel
    ) -> DataAnalysisStateModel:
        logger.info("Calling data_analysis_agent_tools...")
        messages = state["messages"]
        last_message = messages[-1]
        # logger.info(f"Last message: {last_message}")
        dataframe = pd.DataFrame()
        csv_file_paths = state.get("csv_file_paths", None)
        logger.info(f"csv_file_paths: {csv_file_paths}")
        csv_loading_error = None
        if csv_file_paths:
            csv_path = csv_file_paths[0]
            try:
                dataframe = pd.read_csv(csv_path)
            except Exception as error:
                logger.error(f"CSV not loaded: {error}")
                csv_loading_error = (
                    f"Could not load data from {csv_path}. Details: {error}"
                )
        tool_results = []
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            eda_tools = [
                tool_class(dataframe=dataframe) for tool_class in self.eda_tools
            ]
            python_repl = PythonAstREPLTool(globals={"df": dataframe})
            all_tools = eda_tools + [python_repl]
            tool_map = {tool.name: tool for tool in all_tools}
            logger.info(f"Tools available: {list(tool_map.keys())}")
            for tool_call in last_message.tool_calls:
                logger.info(f"tool_call: {tool_call}")
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id")
                # logger.info(
                #     f"Processing tool call: name={tool_name}, args={tool_args}, id={tool_id}"
                # )
                if tool_name in tool_map:
                    try:
                        tool_instance = tool_map[tool_name]
                        output = None

                        if csv_loading_error:
                            output = f"File not loaded during tool execution. {csv_loading_error}"
                        else:
                            if tool_name == "python_repl_ast":
                                code_input = (
                                    tool_args.get("query")
                                    or tool_args.get("code")
                                    or tool_args.get("input")
                                )
                                if not code_input:
                                    logger.error(
                                        f"Missing 'input', 'code', or 'query' for python_repl_ast: {tool_args}"
                                    )
                                    raise ValueError(
                                        "Python REPL requires an 'input', 'code', or 'query' argument."
                                    )
                                output = tool_instance.run(code_input)
                                if isinstance(output, (list, tuple)):
                                    output = json.dumps(output)
                            else:
                                full_tool_call = ToolCall(
                                    name=tool_name,
                                    args=tool_args,
                                    id=tool_id,
                                    type="tool_call",
                                )
                                # logger.info(
                                #     f"Invoking tool with ToolCall: {full_tool_call}"
                                # )
                                output = tool_instance.invoke(full_tool_call)
                                if tool_name == "generate_distribution_tool":
                                    try:
                                        json.loads(output.content)
                                    except json.JSONDecodeError as error:
                                        logger.error(
                                            f"Invalid JSON output from {tool_name}: {error}"
                                        )
                                        output = f"Invalid JSON output from {tool_name}"
                        output_content = (
                            str(output) if output is not None else "No output"
                        )
                        tool_results.append(
                            ToolMessage(
                                content=output_content,
                                tool_call_id=tool_id,
                                name=tool_name,
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        tool_results.append(
                            ToolMessage(
                                content=f"Tool execution failed: {e}",
                                tool_call_id=tool_id,
                                name=tool_name,
                            )
                        )
                else:
                    logger.warning(f"Warning: Unknown tool called: {tool_name}")
                    tool_results.append(
                        ToolMessage(
                            content=f"Tool execution failed because unknown tool {tool_name}",
                            tool_call_id=tool_id,
                            name=tool_name,
                        )
                    )
        else:
            logger.warning("Warning: No tool calls found in last message.")
        new_state = {"messages": messages + tool_results}
        return new_state

    @staticmethod
    def tool_output_node(state: DataAnalysisStateModel):
        logger.info("Calling tool_output...")
        # messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        last_message = state["messages"][-1]
        logger.info(f"Last message: {last_message}")
        csv_file_paths = state.get("csv_file_paths", None)
        logger.info(f"csv_file_paths: {csv_file_paths}")
        if (
            isinstance(last_message, ToolMessage)
            and last_message.name == "unzip_zip_file_tool"
        ):
            pattern = r"csv_file_paths:(.+)"
            match = re.search(pattern, last_message.content)
            if match:
                csv_file_paths_str = match.group(1)
                try:
                    csv_file_paths = eval(csv_file_paths_str)
                    # state["csv_file_paths"] = csv_file_paths
                except Exception as e:
                    logger.error(f"Error parsing csv file paths: {e}")

        is_final_plot = state.get("is_final_plot", None)
        logger.info(f"is_final_plot: {is_final_plot}")
        if (
            isinstance(last_message, ToolMessage)
            and last_message.name == "generate_distribution_tool"
        ):
            if is_final_plot is None or (
                is_final_plot
                and is_final_plot["tool_call_id"] != last_message.tool_call_id
            ):
                json_pattern = r"content='(\{.*\})'"
                json_match = re.search(json_pattern, last_message.content, re.DOTALL)

                json_str = None
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = last_message.content.strip()

                if json_str:
                    try:
                        json_obj = json.loads(json_str)
                        logger.info(
                            f"Valid JSON extracted and loaded: {json.dumps(json_obj, indent=4)[:200]}..."
                        )
                        is_final_plot = {
                            "tool_call_id": last_message.tool_call_id,
                            "status": True,
                        }
                    except json.JSONDecodeError as error:
                        logger.error(
                            f"Extracted string is not valid JSON: {json_str[:200]}..., error: {error}"
                        )
        logger.info(f"is_final_plot: {is_final_plot}")
        return {
            "messages": state["messages"],
            "csv_file_paths": csv_file_paths,
            "is_final_plot": is_final_plot,
        }

    def data_analysis_agent_node(self, state: DataAnalysisStateModel) -> dict:
        logger.info("Calling data_analysis_agent...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        dataframe = pd.DataFrame()
        csv_file_paths = state.get("csv_file_paths", None)
        logger.info(f"csv_file_paths: {csv_file_paths}")
        if csv_file_paths:
            csv_path = csv_file_paths[0]
            try:
                dataframe = pd.read_csv(csv_path)
            except Exception as error:
                logger.error(f"CSV not loaded: {error}")
                new_messages = messages + [
                    AIMessage(content=f"Data not loaded from {csv_path}.")
                ]
                return {"messages": new_messages}
        if dataframe.empty:
            logger.warning("Warning: No dataframe available for analysis.")
            new_messages = messages + [
                AIMessage(content="No data available for analysis.")
            ]
            return {"messages": new_messages}
        eda_tools = [tool_class(dataframe=dataframe) for tool_class in self.eda_tools]
        python_repl = PythonAstREPLTool(globals={"df": dataframe})
        all_tools = eda_tools + [python_repl]
        llm_with_tools = self.data_analysis_agent.chat_model.bind_tools(tools=all_tools)
        new_state = self.agent_node(
            state=state,
            agent=self.data_analysis_agent,
            llm_with_tools=llm_with_tools,
        )
        return new_state

    def cleanup_node(self, state: DataAnalysisStateModel) -> DataAnalysisStateModel:
        is_final_plot = state.get("is_final_plot")
        is_final_plot["status"] = False
        return {"is_final_plot": is_final_plot}

    def route_tool_output(self, state: DataAnalysisStateModel) -> str:
        logger.info("Routing from tool_output...")
        last_tool_message = state["messages"][-1]
        routes_to: str = ""

        if last_tool_message.name in ["unzip_zip_file_tool"]:
            # Unzip tool output should return to the UnzipFileAgent to finalize.
            routes_to = self.unzip_file_agent.name
        elif last_tool_message.name in [
            "python_repl_ast",
            "generate_distribution_tool",
        ]:
            # Output from Data Analysis tools MUST go back to the DataAnalysisAgent
            # for synthesis and potential further tool calls.
            routes_to = self.data_analysis_agent.name
        else:
            # Fallback (e.g., if a tool call was made by the Supervisor or a non-standard case)
            routes_to = self.supervisor_agent.name

        logger.info(f"To {routes_to}...")
        return routes_to

    # def route_tool_output(self, state: DataAnalysisStateModel) -> str:
    #     logger.info("Routing from tool_output...")
    #     routes_to: str = ""
    #     is_final_plot = state.get("is_final_plot", None)
    #     if is_final_plot and is_final_plot["status"]:
    #         routes_to = "cleanup_and_end"
    #     else:
    #         routes_to = self.supervisor_agent.name
    #     logger.info(f"To {routes_to}...")
    #     return routes_to
