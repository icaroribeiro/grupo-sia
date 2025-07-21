from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.layers.business_layer.ai_agents.agents.worker_agents import (
    WorkerAgent_2,
    WorkerAgent_3,
)
from src.layers.business_layer.ai_agents.agents.sub_agent_1 import (
    SubAgent_1,
)
from src.layers.business_layer.ai_agents.graphs.base_subgraph import BaseSubgraph
from src.layers.business_layer.ai_agents.models.state import SubgraphState
from langgraph.prebuilt import ToolNode


class Subgraph_2(BaseSubgraph):
    def __init__(
        self,
        name: str,
        worker_agent_2: WorkerAgent_2,
        worker_agent_3: WorkerAgent_3,
        sub_agent_1: SubAgent_1,
    ):
        super().__init__(
            name=name,
            graph=self.create_graph(
                worker_agent_2=worker_agent_2,
                worker_agent_3=worker_agent_3,
                sub_agent_1=sub_agent_1,
            ),
        )

    def create_graph(
        self,
        worker_agent_2: WorkerAgent_2,
        worker_agent_3: WorkerAgent_3,
        sub_agent_1: SubAgent_1,
    ) -> CompiledStateGraph:
        subgraph_builder = StateGraph(state_schema=SubgraphState)
        subgraph_builder.add_node(
            node=sub_agent_1.name,
            action=self.call_llm_chain(
                name=sub_agent_1.name,
                chain=sub_agent_1.create_llm_chain(
                    [worker_agent_2.name, worker_agent_3.name]
                ),
            ),
        )
        subgraph_builder.add_node(
            node=worker_agent_2.name,
            action=self.call_llm_with_tools(
                name=worker_agent_2.name,
                prompt=worker_agent_2.prompt,
                llm_with_tools=worker_agent_2.llm.bind_tools(worker_agent_2.tools),
                routes_to=sub_agent_1.name,
            ),
        )
        subgraph_builder.add_node(
            node=worker_agent_3.name,
            action=self.call_llm_with_tools(
                name=worker_agent_3.name,
                prompt=worker_agent_3.prompt,
                llm_with_tools=worker_agent_3.llm.bind_tools(worker_agent_3.tools),
                routes_to=sub_agent_1.name,
            ),
        )
        subgraph_builder.add_node(
            node="tools",
            action=ToolNode(worker_agent_2.tools + worker_agent_3.tools),
        )
        subgraph_builder.set_entry_point(key=sub_agent_1.name)
        subgraph_builder.add_conditional_edges(
            source=sub_agent_1.name,
            path=self.route,
            path_map={
                worker_agent_2.name: worker_agent_2.name,
                worker_agent_3.name: worker_agent_3.name,
                "FINISH": END,
            },
        )
        subgraph_builder.add_conditional_edges(
            source=worker_agent_2.name,
            path=self.call_tools(routes_to=sub_agent_1.name),
            path_map={
                "tools": "tools",
                sub_agent_1.name: sub_agent_1.name,
            },
        )
        subgraph_builder.add_conditional_edges(
            source=worker_agent_3.name,
            path=self.call_tools(routes_to=sub_agent_1.name),
            path_map={
                "tools": "tools",
                sub_agent_1.name: sub_agent_1.name,
            },
        )
        subgraph_builder.add_edge(start_key="tools", end_key=sub_agent_1.name)
        subgraph = subgraph_builder.compile(checkpointer=MemorySaver())
        return subgraph
