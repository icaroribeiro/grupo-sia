# from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
# from langchain_core.runnables import Runnable
# from langgraph.graph import END, MessagesState, StateGraph
# from langgraph.prebuilt import ToolNode, tools_condition

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )
# from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow


# class DataIngestionWorkflow(BaseWorkflow):
#     def __init__(self, data_ingestion_agent: Runnable[BaseMessage, BaseMessage]):
#         self.__graph = self.__create_graph(
#             data_ingestion_agent=data_ingestion_agent
#         )

#     # def _agent(self, state: AgentState) -> AgentState:
#     #     self.logger.debug("Running agent node")
#     #     messages = state["messages"]
#     #     response = self.llm.invoke(messages)
#     #     self.logger.debug(f"LLM response: {response}")
#     #     return {"messages": messages + [response]}

#     # async def _tools(self, state: AgentState) -> AgentState:
#     #     self.logger.debug("Running tools node")
#     #     messages = state["messages"]
#     #     last_message = messages[-1]

#     #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#     #         tool = LowerCaseTool()
#     #         results = []
#     #         for tool_call in last_message.tool_calls:
#     #             self.logger.info(
#     #                 f"Executing tool call: {tool_call['name']} with args: {tool_call['args']}"
#     #             )
#     #             result = await tool.acall(**tool_call["args"])
#     #             results.append(
#     #                 AIMessage(content=str(result), tool_call_id=tool_call["id"])
#     #             )
#     #         self.logger.debug(f"Tool execution results: {results}")
#     #         return {"messages": messages + results}
#     #     return state

#     def _should_continue(self, state: MessagesState) -> str:
#         messages = state["messages"]
#         last_message = messages[-1]
#         if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#             self.logger.debug("Routing to tools node")
#             return "tools"
#         self.logger.debug("Routing to END")
#         return END

#     def __create_graph(
#         self, data_ingestion_agent: Runnable[BaseMessage, BaseMessage]
#     ) -> StateGraph:
#         workflow = StateGraph(MessagesState)
#         workflow.add_node(
#             "data_ingestion_agent",
#             self.create_agent_node(
#                 name="data_ingestion_agent",
#                 agent=data_ingestion_agent,
#                 system_message=SystemMessage(
#                     content="You are a helpful assistant tasked with finding Icaro's age."
#                 ),
#             ),
#         )
#         workflow.add_node("tools", ToolNode([GetIcarosAgeTool()]))
#         workflow.set_entry_point("data_ingestion_agent")
#         workflow.add_conditional_edges(
#             "data_ingestion_agent",
#             tools_condition,
#             # self._should_continue,
#             # {"tools": "tools", END: END}
#         )
#         workflow.add_edge("tools", "data_ingestion_agent")
#         return workflow.compile()

#     async def arun(self, input_message: str) -> dict:
#         input_messages = [HumanMessage(content=input_message)]
#         result = await self.__graph.ainvoke({"messages": input_messages})
#         return result
