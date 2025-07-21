from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.layers.business_layer.ai_agents.agents.worker_agents import (
    WorkerAgent_1,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph import END
from src.layers.business_layer.ai_agents.graphs.base_subgraph import BaseSubgraph
from src.layers.business_layer.ai_agents.models.state import SubgraphState


class Subgraph_1(BaseSubgraph):
    def __init__(
        self,
        name: str,
        worker_agent_1: WorkerAgent_1,
    ):
        super().__init__(
            name=name,
            graph=self.create_graph(worker_agent_1=worker_agent_1),
        )

    def create_graph(
        self,
        worker_agent_1: WorkerAgent_1,
    ) -> CompiledStateGraph:
        subgraph_builder = StateGraph(state_schema=SubgraphState)
        subgraph_builder.add_node(
            node=worker_agent_1.name,
            action=self.call_llm_with_tools(
                name=worker_agent_1.name,
                prompt=worker_agent_1.prompt,
                llm_with_tools=worker_agent_1.llm.bind_tools(worker_agent_1.tools),
                routes_to=END,
            ),
        )
        subgraph_builder.add_node(node="tools", action=ToolNode(worker_agent_1.tools))
        subgraph_builder.set_entry_point(key=worker_agent_1.name)
        subgraph_builder.add_conditional_edges(
            source=worker_agent_1.name,
            path=self.call_tools(routes_to=END),
            path_map={"tools": "tools", END: END},
        )
        subgraph_builder.add_edge(start_key="tools", end_key=worker_agent_1.name)
        subgraph = subgraph_builder.compile(checkpointer=MemorySaver())
        return subgraph
