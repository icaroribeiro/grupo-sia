from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.layers.business_layer.ai_agents.agents.manager_agent_1 import ManagerAgent_1
from src.layers.business_layer.ai_agents.graphs.base_parent_graph import BaseParentGraph
from src.layers.business_layer.ai_agents.graphs.subgraph_2 import Subgraph_2
from src.layers.business_layer.ai_agents.models.state import ParentGraphState
from langgraph.graph import END


class ParentGraph_1(BaseParentGraph):
    def __init__(
        self,
        name: str,
        subgraph_2: Subgraph_2,
        manager_agent_1: ManagerAgent_1,
    ):
        super().__init__(
            name=name,
            graph=self.create_graph(
                subgraph_2=subgraph_2,
                manager_agent_1=manager_agent_1,
            ),
        )

    def create_graph(
        self,
        subgraph_2: Subgraph_2,
        manager_agent_1: ManagerAgent_1,
    ) -> CompiledStateGraph:
        parentgraph_builder = StateGraph(state_schema=ParentGraphState)
        parentgraph_builder.add_node(
            node=manager_agent_1.name,
            action=self.call_node(
                name=manager_agent_1.name,
                node_chain=manager_agent_1.create_chain([subgraph_2.name]),
            ),
        )
        parentgraph_builder.add_node(
            node=subgraph_2.name,
            action=self.call_subgraph(
                name=subgraph_2.name,
                subgraph=subgraph_2,
                routes_to=manager_agent_1.name,
            ),
        )
        parentgraph_builder.set_entry_point(key=manager_agent_1.name)
        parentgraph_builder.add_conditional_edges(
            source=manager_agent_1.name,
            path=self.route,
            path_map={
                subgraph_2.name: subgraph_2.name,
                "FINISH": END,
            },
        )
        parentgraph_builder.add_edge(
            start_key=subgraph_2.name, end_key=manager_agent_1.name
        )
        parentgraph = parentgraph_builder.compile(checkpointer=MemorySaver())
        print(parentgraph.get_graph().draw_ascii())
        return parentgraph
