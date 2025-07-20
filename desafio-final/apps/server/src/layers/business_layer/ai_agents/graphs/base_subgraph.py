import functools
import uuid

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.runnables import Runnable

from src.layers.business_layer.ai_agents.models.state import (
    SubgraphState,
)
from src.layers.core_logic_layer.logging import logger
from langgraph.graph.state import CompiledStateGraph


class BaseSubgraph:
    def __init__(
        self,
        name: str,
        graph: CompiledStateGraph,
    ):
        self.name: str = name
        self.__graph: CompiledStateGraph = graph

    def call_subnode(
        self,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[list[BaseMessage], BaseMessage],
        routes_to: str,
    ) -> SubgraphState:
        return functools.partial(
            self.__subnode,
            name=name,
            prompt=prompt,
            llm_with_tools=llm_with_tools,
            routes_to=routes_to,
        )

    def call_node(
        self,
        name: str,
        node_chain: Runnable[dict[str, list[BaseMessage]], dict[str, str]],
    ) -> SubgraphState:
        return functools.partial(
            self.__node,
            name=name,
            node_chain=node_chain,
        )

    def call_tool(self, routes_to: str) -> str:
        return functools.partial(self.__tool, routes_to=routes_to)

    def route(self, state: SubgraphState) -> str:
        next_agent = state["next"]
        logger.info(f"Routing to {next_agent}...")
        return next_agent

    async def run(self, input_message: str, next: str) -> dict:
        logger.info(
            f"Started running {self.name} with input_message: {input_message}..."
        )
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        result = await self.__graph.ainvoke(
            {
                "messages": input_messages,
                "next": next,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        logger.info(f"Workflow result: {result}")
        return result

    @staticmethod
    def __subnode(
        state: SubgraphState,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[list[BaseMessage], BaseMessage],
        routes_to: str,
    ) -> SubgraphState:
        logger.info(f"Started running {name}...")
        messages = state["messages"]
        logger.info(f"{name} input messages: {messages}")
        response = llm_with_tools.invoke([SystemMessage(content=prompt)] + messages)
        logger.info(f"{name} response: {response}")
        return {
            "messages": messages + [response],
            "next": "tools"
            if hasattr(response, "tool_calls") and response.tool_calls
            else routes_to,
        }

    @staticmethod
    def __node(
        state: SubgraphState,
        name: str,
        node_chain: Runnable[dict[str, list[BaseMessage]], dict[str, str]],
    ) -> SubgraphState:
        logger.info(f"Started running {name}...")
        messages = state["messages"]
        logger.info(f"{name} input messages: {messages}")
        response = node_chain.invoke({"messages": messages})
        logger.info(f"{name} response: {response}")
        return {"messages": messages, "next": response["next"]}

    @staticmethod
    def __tool(
        state: SubgraphState,
        routes_to: str,
    ) -> str:
        last_message = state["messages"][-1]
        logger.info(f"Last message: {last_message}")
        return (
            "tools"
            if hasattr(last_message, "tool_calls") and last_message.tool_calls
            else routes_to
        )
