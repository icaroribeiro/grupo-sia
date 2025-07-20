# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import END, StateGraph
# from langgraph.prebuilt import ToolNode

# from src.layers.business_layer.ai_agents.agents.assistant_agents import (
#     AssistentAgent_1,
#     Agent2,
#     Agent3,
# )
# from src.layers.business_layer.ai_agents.agents.sub_agent_1 import SubAgent_1
# from src.layers.business_layer.ai_agents.models.state import AgentState
# from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow


# class TestWorkflow(BaseWorkflow):
#     def __init__(
#         self,
#         name: str,
#         assistant_agent_1: AssistentAgent_1,
#         agent2: Agent2,
#         agent3: Agent3,
#         sub_agent_1: SubAgent_1,
#     ):
#         super().__init__(
#             name=name,
#             graph=self.create_graph(
#                 assistant_agent_1=assistant_agent_1,
#                 agent2=agent2,
#                 agent3=agent3,
#                 sub_agent_1=sub_agent_1,
#             ),
#         )

#     def create_graph(
#         self,
#         assistant_agent_1: AssistentAgent_1,
#         agent2: Agent2,
#         agent3: Agent3,
#         sub_agent_1: SubAgent_1,
#     ) -> StateGraph:
#         workflow = StateGraph(state_schema=AgentState)
#         # workflow.add_node(
#         #     node=assistant_agent_1.name,
#         #     action=self.create_agent_node(
#         #         name=assistant_agent_1.name,
#         #         prompt=assistant_agent_1.prompt,
#         #         llm_with_tools=assistant_agent_1.llm.bind_tools(assistant_agent_1.tools),
#         #     ),
#         # )
#         # workflow.add_node(node="tools", action=ToolNode(assistant_agent_1.tools))
#         # workflow.set_entry_point(key=assistant_agent_1.name)
#         # workflow.add_conditional_edges(
#         #     source=assistant_agent_1.name,
#         #     path=tools_condition,
#         # )
#         # workflow.add_edge("tools", assistant_agent_1.name)
#         workflow.add_node(
#             node="supervisor",
#             action=self.create_supervisor_node(
#                 name=sub_agent_1.name,
#                 supervisor_chain=sub_agent_1.create_supervisor_chain(
#                     [assistant_agent_1.name]
#                 ),
#             ),
#         )
#         workflow.add_node(
#             node=assistant_agent_1.name,
#             action=self.create_agent_node(
#                 name=assistant_agent_1.name,
#                 prompt=assistant_agent_1.prompt,
#                 llm_with_tools=assistant_agent_1.llm.bind_tools(assistant_agent_1.tools),
#             ),
#         )
#         # workflow.add_node(
#         #     agent2.name,
#         #     self.create_agent_node(
#         #         name=agent2.name,
#         #         prompt=agent2.prompt,
#         #         llm_with_tools=agent2.llm.bind_tools(agent2.tools),
#         #     ),
#         # )
#         # workflow.add_node(
#         #     agent3.name,
#         #     self.create_agent_node(
#         #         name=agent3.name,
#         #         prompt=agent3.prompt,
#         #         llm_with_tools=agent3.llm.bind_tools(agent3.tools),
#         #     ),
#         # )
#         # workflow.add_node("tools", ToolNode(assistant_agent_1.tools + agent2.tools + agent3.tools))
#         workflow.add_node(node="tools", action=ToolNode(assistant_agent_1.tools))
#         workflow.set_entry_point(key="supervisor")
#         workflow.add_conditional_edges(
#             source="supervisor",
#             path=self.route,
#             path_map={
#                 assistant_agent_1.name: assistant_agent_1.name,
#                 # agent2.name: agent2.name,
#                 # agent3.name: agent3.name,
#                 "FINISH": END,
#             },
#         )
#         workflow.add_conditional_edges(
#             source=assistant_agent_1.name,
#             path=self.tools_condition,
#             path_map={"tools": "tools", "supervisor": "supervisor"},
#         )
#         # workflow.add_conditional_edges(
#         #     agent2.name,
#         #     self.tools_condition,
#         #     {"tools": "tools", "supervisor": "supervisor"},
#         # )
#         # workflow.add_conditional_edges(
#         #     agent3.name,
#         #     self.tools_condition,
#         #     {"tools": "tools", "supervisor": "supervisor"},
#         # )
#         workflow.add_edge(start_key="tools", end_key=assistant_agent_1.name)
#         # workflow.add_edge(start_key=assistant_agent_1.name, end_key="supervisor")
#         return workflow.compile(checkpointer=MemorySaver())
