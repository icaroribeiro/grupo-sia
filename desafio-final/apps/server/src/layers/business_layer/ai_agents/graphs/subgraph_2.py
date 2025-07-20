from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.layers.business_layer.ai_agents.agents.assistant_agents import (
    AssistentAgent_2,
    AssistentAgent_3,
)
from src.layers.business_layer.ai_agents.agents.supervisor_agent_1 import (
    SupervisorAgent_1,
)
from src.layers.business_layer.ai_agents.graphs.base_subgraph import BaseSubgraph
from src.layers.business_layer.ai_agents.models.state import SubgraphState
from langgraph.prebuilt import ToolNode


class Subgraph_2(BaseSubgraph):
    def __init__(
        self,
        name: str,
        assistant_agent_2: AssistentAgent_2,
        assistant_agent_3: AssistentAgent_3,
        supervisor_agent_1: SupervisorAgent_1,
    ):
        super().__init__(
            name=name,
            graph=self.create_graph(
                assistant_agent_2=assistant_agent_2,
                assistant_agent_3=assistant_agent_3,
                supervisor_agent_1=supervisor_agent_1,
            ),
        )

    def create_graph(
        self,
        assistant_agent_2: AssistentAgent_2,
        assistant_agent_3: AssistentAgent_3,
        supervisor_agent_1: SupervisorAgent_1,
    ) -> CompiledStateGraph:
        subgraph_builder = StateGraph(state_schema=SubgraphState)
        subgraph_builder.add_node(
            node=supervisor_agent_1.name,
            action=self.call_node(
                name=supervisor_agent_1.name,
                node_chain=supervisor_agent_1.create_chain(
                    [assistant_agent_2.name, assistant_agent_3.name]
                ),
            ),
        )
        subgraph_builder.add_node(
            node=assistant_agent_2.name,
            action=self.call_subnode(
                name=assistant_agent_2.name,
                prompt=assistant_agent_2.prompt,
                llm_with_tools=assistant_agent_2.llm.bind_tools(
                    assistant_agent_2.tools
                ),
                routes_to=supervisor_agent_1.name,
            ),
        )
        subgraph_builder.add_node(
            node=assistant_agent_3.name,
            action=self.call_subnode(
                name=assistant_agent_3.name,
                prompt=assistant_agent_3.prompt,
                llm_with_tools=assistant_agent_3.llm.bind_tools(
                    assistant_agent_3.tools
                ),
                routes_to=supervisor_agent_1.name,
            ),
        )
        subgraph_builder.add_node(
            node="tools",
            action=ToolNode(assistant_agent_2.tools + assistant_agent_3.tools),
        )
        subgraph_builder.set_entry_point(key=supervisor_agent_1.name)
        subgraph_builder.add_conditional_edges(
            source=supervisor_agent_1.name,
            path=self.route,
            path_map={
                assistant_agent_2.name: assistant_agent_2.name,
                assistant_agent_3.name: assistant_agent_3.name,
                "FINISH": END,
            },
        )
        subgraph_builder.add_conditional_edges(
            source=assistant_agent_2.name,
            path=self.call_tool(routes_to=supervisor_agent_1.name),
            path_map={
                "tools": "tools",
                supervisor_agent_1.name: supervisor_agent_1.name,
            },
        )
        subgraph_builder.add_conditional_edges(
            source=assistant_agent_3.name,
            path=self.call_tool(routes_to=supervisor_agent_1.name),
            path_map={
                "tools": "tools",
                supervisor_agent_1.name: supervisor_agent_1.name,
            },
        )
        subgraph_builder.add_edge(start_key="tools", end_key=supervisor_agent_1.name)
        subgraph = subgraph_builder.compile(checkpointer=MemorySaver())
        print(subgraph.get_graph().draw_ascii())
        return subgraph
