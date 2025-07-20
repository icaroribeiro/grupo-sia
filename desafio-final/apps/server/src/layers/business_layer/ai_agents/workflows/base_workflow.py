# import functools
# import uuid
# from abc import ABC, abstractmethod

# from langchain_core.messages import (
#     BaseMessage,
#     HumanMessage,
#     SystemMessage,
# )
# from langchain_core.runnables import Runnable
# from langgraph.graph import StateGraph

# from src.layers.business_layer.ai_agents.models.state import AgentState
# from src.layers.core_logic_layer.logging import logger


# class BaseWorkflow(ABC):
#     def __init__(
#         self,
#         name: str,
#         graph: StateGraph,
#     ):
#         self.__name: str = name
#         self.__graph: StateGraph = graph

#     @abstractmethod
#     def create_graph(self, *args, **kwargs) -> StateGraph:
#         raise Exception("NotImplementedException")

#     def create_supervisor_node(
#         self,
#         name: str,
#         supervisor_chain: Runnable[dict[str, list[BaseMessage]], dict[str, str]],
#     ) -> AgentState:
#         return functools.partial(
#             self.__supervisor_node,
#             name=name,
#             supervisor_chain=supervisor_chain,
#         )

#     def create_agent_node(
#         self, name: str, prompt: str, llm_with_tools: Runnable[BaseMessage, BaseMessage]
#     ) -> AgentState:
#         return functools.partial(
#             self.__agent_node, name=name, prompt=prompt, llm_with_tools=llm_with_tools
#         )

#     def route(self, state: AgentState) -> str:
#         next_agent = state["next"]
#         logger.info(f"Routing to {next_agent}...")
#         return next_agent

#     def tools_condition(self, state: AgentState) -> str:
#         last_message = state["messages"][-1]
#         logger.info(f"Last message: {last_message}")
#         return (
#             "tools"
#             if hasattr(last_message, "tool_calls") and last_message.tool_calls
#             else "supervisor"
#         )

#     async def run(self, input_message: str) -> dict:
#         logger.info(
#             f"Started running {self.__name} workflow with input_message: {input_message}..."
#         )
#         input_messages = [HumanMessage(content=input_message)]
#         thread_id = str(uuid.uuid4())
#         result = await self.__graph.ainvoke(
#             {"messages": input_messages, "next": "supervisor"},
#             config={"configurable": {"thread_id": thread_id}},
#         )
#         logger.info(f"Workflow result: {result}")
#         return result

#     @staticmethod
#     def __supervisor_node(
#         state: AgentState,
#         name: str,
#         supervisor_chain: Runnable[dict[str, list[BaseMessage]], dict[str, str]],
#     ) -> AgentState:
#         logger.info(f"Started running {name}...")
#         messages = state["messages"]
#         logger.info(f"{name} input messages: {messages}")
#         response = supervisor_chain.invoke({"messages": messages})
#         logger.info(f"{name} response: {response}")
#         return {"messages": messages, "next": response["next"]}

#     @staticmethod
#     def __agent_node(
#         state: AgentState,
#         name: str,
#         prompt: str,
#         llm_with_tools: Runnable[BaseMessage, BaseMessage],
#     ) -> AgentState:
#         logger.info(f"Started running {name}...")
#         messages = state["messages"]
#         logger.info(f"{name} input messages: {messages}")
#         response = llm_with_tools.invoke([SystemMessage(content=prompt)] + messages)
#         logger.info(f"{name} response: {response}")
#         return {
#             "messages": messages + [response],
#             "next": "tools"
#             if hasattr(response, "tool_calls") and response.tool_calls
#             else "supervisor",
#         }
