from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.layers.business_layer.ai_agents.agents.assistant_agents import (
    AssistentAgent_1,
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
        assistant_agent_1: AssistentAgent_1,
    ):
        super().__init__(
            name=name,
            graph=self.create_graph(assistant_agent_1=assistant_agent_1),
        )

    def create_graph(
        self,
        assistant_agent_1: AssistentAgent_1,
    ) -> CompiledStateGraph:
        subgraph_builder = StateGraph(state_schema=SubgraphState)
        subgraph_builder.add_node(
            node=assistant_agent_1.name,
            action=self.call_assistant_node(
                name=assistant_agent_1.name,
                prompt=assistant_agent_1.prompt,
                llm_with_tools=assistant_agent_1.llm.bind_tools(
                    assistant_agent_1.tools
                ),
                routes_to=END,
            ),
        )
        subgraph_builder.add_node(
            node="tools", action=ToolNode(assistant_agent_1.tools)
        )
        subgraph_builder.set_entry_point(key=assistant_agent_1.name)
        subgraph_builder.add_conditional_edges(
            source=assistant_agent_1.name,
            path=self.call_tool_node(routes_to=END),
            path_map={"tools": "tools", END: END},
        )
        subgraph_builder.add_edge(start_key="tools", end_key=assistant_agent_1.name)
        subgraph = subgraph_builder.compile(checkpointer=MemorySaver())
        return subgraph
