import functools

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.agents.data_analysis_supervisor_agent import (
    DataAnalysisSupervisorAgent,
)
from src.layers.business_layer.ai_agents.models.data_analysis_state_graph_model import (
    DataAnalysisStateGraphModel,
)
from src.layers.business_layer.ai_agents.models.data_analysis_state_model import (
    DataAnalysisStateModel,
)
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow


class DataAnalysisWorkflow(BaseWorkflow):
    def __init__(
        self,
        async_sql_database_tools: list[BaseTool],
        data_analysis_agent: DataAnalysisAgent,
        data_analysis_supervisor_agent: DataAnalysisSupervisorAgent,
        delegate_to_data_analysis_agent_tool: DataAnalysisHandoffTool,
    ):
        self.name = "data_analysis_workflow"
        self.data_analysis_agent_tools = async_sql_database_tools
        self.data_analysis_agent = data_analysis_agent
        self.data_analysis_supervisor_agent = data_analysis_supervisor_agent
        self.delegate_to_data_analysis_agent_tool = delegate_to_data_analysis_agent_tool

    def _build_workflow(self) -> DataAnalysisStateGraphModel:
        builder = StateGraph(state_schema=DataAnalysisStateModel)
        self.__add_nodes(builder)
        self.__add_edges(builder)
        self.__add_conditional_edges(builder)
        return DataAnalysisStateGraphModel(name=self.name, graph=builder)

    def __add_nodes(self, builder: StateGraph) -> None:
        builder.add_node(
            node="tools",
            action=ToolNode(tools=self.data_analysis_agent_tools),
        )
        builder.add_node(
            node=self.data_analysis_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.data_analysis_agent,
                llm_with_tools=self.data_analysis_agent.chat_model.bind_tools(
                    tools=self.data_analysis_agent_tools,
                ),
            ),
        )
        builder.add_node(
            node=self.data_analysis_supervisor_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.data_analysis_supervisor_agent,
                llm_with_tools=self.data_analysis_supervisor_agent.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_data_analysis_agent_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="handoff_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_data_analysis_agent_tool,
                ]
            ),
        )
        builder.add_node(
            node="handoff_node",
            action=functools.partial(
                self.handoff_node, agent=self.data_analysis_supervisor_agent
            ),
        )

    def __add_edges(self, builder: StateGraph) -> None:
        builder.add_edge(
            start_key=START, end_key=self.data_analysis_supervisor_agent.name
        )
        # builder.add_edge(start_key="tools", end_key="data_analysis_agent")
        builder.add_edge(start_key="handoff_tools", end_key="handoff_node")

    def __add_conditional_edges(self, builder: StateGraph) -> None:
        builder.add_conditional_edges(
            source=self.data_analysis_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.data_analysis_agent.name,
                routes_to=self.data_analysis_supervisor_agent.name,
            ),
            path_map={
                "tools": "tools",
                self.data_analysis_supervisor_agent.name: self.data_analysis_supervisor_agent.name,
            },
        )
        builder.add_conditional_edges(
            source=self.data_analysis_supervisor_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.data_analysis_supervisor_agent.name,
                routes_to=END,
                is_handoff=True,
            ),
            path_map={"handoff_tools": "handoff_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                self.data_analysis_agent.name: self.data_analysis_agent.name,
                self.data_analysis_supervisor_agent.name: self.data_analysis_supervisor_agent.name,
            },
        )
