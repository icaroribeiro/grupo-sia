import functools
from langgraph.graph import START, StateGraph, END
from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent
from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from langgraph.prebuilt import ToolNode
from src.layers.business_layer.ai_agents.agents.supervisor_agent import SupervisorAgent
from src.layers.business_layer.ai_agents.agents.unzip_file_agent import UnzipFileAgent
from src.layers.business_layer.ai_agents.models.data_analysis_state_model import (
    DataAnalysisStateModel,
)
from src.layers.business_layer.ai_agents.models.state_graph_model import StateGraphModel
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
import re
import pandas as pd
from langchain_core.messages import AIMessage
from langchain.agents.agent_types import AgentType
from langchain.agents import AgentExecutor
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from src.layers.core_logic_layer.logging import logger


class DataAnalysisWorkflow(BaseWorkflow):
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings,
        unzip_file_agent: UnzipFileAgent,
        data_analysis_agent: DataAnalysisAgent,
        supervisor_agent: SupervisorAgent,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
    ) -> None:
        super().__init__()
        self.name = "data_analysis_workflow"
        self.streamlit_app_settings = streamlit_app_settings
        self.unzip_file_agent = unzip_file_agent
        self.data_analysis_agent = data_analysis_agent
        self.supervisor_agent = supervisor_agent
        self.unzip_files_from_zip_archive_tool = unzip_files_from_zip_archive_tool
        self.delegate_to_unzip_file_agent = DataAnalysisHandoffTool(
            agent_name=unzip_file_agent.name,
        )
        self.delegate_to_data_analysis_agent = DataAnalysisHandoffTool(
            agent_name=data_analysis_agent.name,
        )

    #     self._workflow: StateGraphModel | None = None

    # @property
    # def workflow(self) -> StateGraph:
    #     if self._workflow is None:
    #         self._workflow = self._build_workflow()
    #     return self._workflow.graph

    def _build_workflow(self) -> StateGraphModel:
        builder = StateGraph(state_schema=DataAnalysisStateModel)
        self._add_nodes(builder)
        self._add_edges(builder)
        self._add_conditional_edges(builder)
        return StateGraphModel(name=self.name, graph=builder)

    def _add_nodes(self, builder: StateGraph) -> None:
        builder.add_node(
            node=self.unzip_file_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.unzip_file_agent,
                llm_with_tools=self.unzip_file_agent.chat_model.bind_tools(
                    tools=[self.unzip_files_from_zip_archive_tool]
                ),
            ),
        )
        builder.add_node(
            node=self.data_analysis_agent.name,
            action=functools.partial(
                self.data_analysis_node,
                agent=self.data_analysis_agent,
            ),
        )
        builder.add_node(
            node=self.supervisor_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.supervisor_agent,
                llm_with_tools=self.supervisor_agent.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_unzip_file_agent,
                        self.delegate_to_data_analysis_agent,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="tools",
            action=ToolNode(tools=[self.unzip_files_from_zip_archive_tool]),
        )
        builder.add_node(
            node="supervisor_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_unzip_file_agent,
                    self.delegate_to_data_analysis_agent,
                ]
            ),
        )
        builder.add_node("tool_output_node", self.tool_output_node)
        builder.add_node("handoff_node", self.handoff_node)

    def _add_edges(self, builder: StateGraph) -> None:
        builder.add_edge(start_key=START, end_key=self.supervisor_agent.name)
        builder.add_edge(start_key="supervisor_tools", end_key="handoff_node")
        builder.add_edge(start_key="tools", end_key="tool_output_node")
        builder.add_edge(
            start_key="tool_output_node", end_key=self.supervisor_agent.name
        )

    def _add_conditional_edges(self, builder: StateGraph) -> None:
        builder.add_conditional_edges(
            source=self.supervisor_agent.name,
            path=functools.partial(
                self.route_supervisor, name=self.supervisor_agent.name
            ),
            path_map={"supervisor_tools": "supervisor_tools", END: END},
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
        builder.add_conditional_edges(
            source=self.unzip_file_agent.name,
            path=functools.partial(
                self.route_agent,
                name=self.unzip_file_agent.name,
                routes_to_by_tool_name=None,
            ),
            path_map={
                "tools": "tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.data_analysis_agent.name,
            path=functools.partial(
                self.route_agent,
                name=self.data_analysis_agent.name,
                routes_to_by_tool_name=None,
            ),
            path_map={
                "tools": "tools",
                self.supervisor_agent.name: self.supervisor_agent.name,
            },
        )

    def data_analysis_node(
        self,
        state: DataAnalysisStateModel,
        agent: BaseAgent,
    ) -> DataAnalysisStateModel:
        # logger.info(f"Calling {agent.name}...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")

        csv_file_paths = state.get("csv_file_paths", [])
        if not csv_file_paths:
            logger.warning("No csv file paths found in state. Skipping data analysis.")
        #     return {"messages": messages}

        dataframes: list[pd.DataFrame] = []
        for csv_file_path in csv_file_paths:
            dataframes.append(pd.read_csv(filepath_or_buffer=csv_file_path))
        if len(dataframes):
            logger.warning(f"{len(dataframes)} dataframes read for data analysis.")

        agent_executor: AgentExecutor = create_pandas_dataframe_agent(
            llm=self.data_analysis_agent.chat_model,
            df=dataframes,
            # agent_type="tool-calling",
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=agent.prompt,
            verbose=True,
        )

        response = agent_executor.invoke(messages)
        # logger.info(f"{name} response: {response}")

        # It's to deduplicate tool calls before updating the state by ensuring that
        # only unique tool calls (based on name and arguments) are passed to
        # the tools node.
        if hasattr(response, "tool_calls") and response.tool_calls:
            seen = set()
            unique_tool_calls = []
            for tool_call in response.tool_calls:
                tool_key = (tool_call["name"], str(tool_call["args"]))
                if tool_key not in seen:
                    seen.add(tool_key)
                    unique_tool_calls.append(tool_call)
            response.tool_calls = unique_tool_calls

        response_dict = agent_executor.invoke(messages)
        final_output = response_dict.get("output", "No response generated.")
        new_messages = messages + [AIMessage(content=final_output)]
        return {"messages": new_messages}

    @staticmethod
    def tool_output_node(state: DataAnalysisStateModel):
        # messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")

        if "csv_file_paths" in last_message.content:
            pattern = r"csv_file_paths:(.+)"
            match = re.search(pattern, last_message.content)
            if match:
                csv_file_paths_str = match.group(1)
                try:
                    csv_file_paths = eval(csv_file_paths_str)
                    state["csv_file_paths"] = csv_file_paths
                except Exception as e:
                    logger.error(f"Error parsing csv file paths: {e}")

        return state
