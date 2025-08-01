from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.layers.business_layer.ai_agents.agents.parent_agent_1 import ParentAgent_1
from src.layers.business_layer.ai_agents.graphs.base_parent_graph import BaseParentGraph
from src.layers.business_layer.ai_agents.graphs.subgraph_2 import Subgraph_2
from src.layers.business_layer.ai_agents.models.state import ParentGraphState


class ParentGraph_1(BaseParentGraph):
    def __init__(
        self,
        name: str,
        subgraph_2: Subgraph_2,
        parent_agent_1: ParentAgent_1,
    ):
        super().__init__(
            name=name,
            graph=self.create_graph(
                subgraph_2=subgraph_2,
                parent_agent_1=parent_agent_1,
            ),
        )

    def create_graph(
        self,
        subgraph_2: Subgraph_2,
        parent_agent_1: ParentAgent_1,
    ) -> CompiledStateGraph:
        parentgraph_builder = StateGraph(state_schema=ParentGraphState)
        parentgraph_builder.add_node(
            node=parent_agent_1.name,
            action=self.call_llm_chain(
                name=parent_agent_1.name,
                chain=parent_agent_1.create_llm_chain([subgraph_2.name]),
            ),
        )
        parentgraph_builder.add_node(
            node=subgraph_2.name,
            action=self.call_subgraph_node(
                name=subgraph_2.name,
                subgraph=subgraph_2,
                routes_to=parent_agent_1.name,
            ),
        )
        parentgraph_builder.set_entry_point(key=parent_agent_1.name)
        parentgraph_builder.add_conditional_edges(
            source=parent_agent_1.name,
            path=self.route,
            path_map={
                subgraph_2.name: subgraph_2.name,
                "FINISH": END,
            },
        )
        parentgraph_builder.add_edge(
            start_key=subgraph_2.name, end_key=parent_agent_1.name
        )
        parentgraph = parentgraph_builder.compile(checkpointer=MemorySaver())
        print(parentgraph.get_graph(xray=True).draw_ascii())
        return parentgraph
