import functools

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.layers.business_layer.ai_agents.agents.manager_agent import (
    ManagerAgent,
)
from src.layers.business_layer.ai_agents.models.top_level_state_graph_model import (
    TopLevelStateGraphModel,
)
from src.layers.business_layer.ai_agents.models.top_level_state_model import (
    TopLevelStateModel,
)
from src.layers.business_layer.ai_agents.tools.top_level_handoff_tool import (
    TopLevelHandoffTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)


class TopLevelWorkflow(BaseWorkflow):
    def __init__(
        self,
        data_ingestion_workflow: DataIngestionWorkflow,
        data_analysis_workflow: DataAnalysisWorkflow,
        manager_agent: ManagerAgent,
        delegate_to_data_ingestion_workflow_tool: TopLevelHandoffTool,
        delegate_to_data_analysis_workflow_tool: TopLevelHandoffTool,
    ):
        self.name = "top_level_workflow"
        self.data_ingestion_workflow = data_ingestion_workflow
        self.data_analysis_workflow = data_analysis_workflow
        self.manager_agent = manager_agent
        self.delegate_to_data_ingestion_workflow_tool = (
            delegate_to_data_ingestion_workflow_tool
        )
        self.delegate_to_data_analysis_workflow_tool = (
            delegate_to_data_analysis_workflow_tool
        )

    def _build_workflow(self) -> TopLevelStateGraphModel:
        builder = StateGraph(state_schema=TopLevelStateModel)
        self.__add_nodes(builder)
        self.__add_edges(builder)
        self.__add_conditional_edges(builder)
        return TopLevelStateGraphModel(name=self.name, graph=builder)

    def __add_nodes(self, builder: StateGraph) -> None:
        builder.add_node(
            node=self.manager_agent.name,
            action=functools.partial(
                self.agent_node,
                agent=self.manager_agent,
                llm_with_tools=self.manager_agent.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_data_ingestion_workflow_tool,
                        self.delegate_to_data_analysis_workflow_tool,
                    ]
                ),
            ),
        )
        builder.add_node(
            node=self.data_ingestion_workflow.name,
            action=self.call_data_ingestion_workflow,
        )
        builder.add_node(
            node=self.data_analysis_workflow.name,
            action=self.call_data_analysis_workflow,
        )
        builder.add_node(
            node="handoff_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_data_ingestion_workflow_tool,
                    self.delegate_to_data_analysis_workflow_tool,
                ]
            ),
        )
        builder.add_node(
            node="handoff_node",
            action=functools.partial(self.handoff_node, agent=self.manager_agent),
        )

    def __add_edges(self, builder: StateGraph) -> None:
        builder.add_edge(start_key=START, end_key=self.manager_agent.name)
        builder.add_edge(start_key="tools", end_key="handoff_node")

    def __add_conditional_edges(self, builder: StateGraph) -> None:
        builder.add_conditional_edges(
            source=self.manager_agent.name,
            path=functools.partial(
                self.route_tools,
                name=self.manager_agent.name,
                routes_to=END,
                is_handoff=True,
            ),
            path_map={"handoff_tools": "handoff_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                self.data_ingestion_workflow.name: self.data_ingestion_workflow.name,
                self.data_analysis_workflow.name: self.data_analysis_workflow.name,
                self.manager_agent.name: self.manager_agent.name,
            },
        )

    async def call_data_ingestion_workflow(
        self, state: TopLevelStateModel
    ) -> TopLevelStateModel:
        return await self.data_ingestion_workflow.run(state=state)

    async def call_data_analysis_workflow(
        self, state: TopLevelStateModel
    ) -> TopLevelStateModel:
        return await self.data_analysis_workflow.run(state=state)
