import functools
import uuid
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END
from langchain_core.runnables import Runnable
from src.layers.business_layer.ai_agents.models.state import ParentGraphState
from src.layers.business_layer.ai_agents.graphs.base_subgraph import BaseSubgraph
from src.layers.core_logic_layer.logging import logger
from langgraph.graph.state import CompiledStateGraph
from src.layers.business_layer.ai_agents.models.state import (
    SubgraphState,
)


class BaseParentGraph:
    def __init__(
        self,
        name: str,
        graph: CompiledStateGraph,
    ):
        self.name: str = name
        self.__graph: CompiledStateGraph = graph

    def call_subgraph_node(
        self, name: str, subgraph: BaseSubgraph, routes_to: str = END
    ) -> SubgraphState:
        return functools.partial(
            self.__call_subgraph_node,
            name=name,
            subgraph=subgraph,
            routes_to=routes_to,
        )

    def call_node_with_chain(
        self,
        name: str,
        chain: Runnable[dict[str, list[BaseMessage]], dict[str, str]],
    ) -> SubgraphState:
        return functools.partial(
            self.__call_node_with_chain,
            name=name,
            chain=chain,
        )

    def route(self, state: ParentGraphState) -> str:
        next_node = state["next"]
        logger.info(f"Routing to {next_node}...")
        return next_node

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
        logger.info(f"{self.name} result: {result}")
        return result

    @staticmethod
    async def __call_subgraph_node(
        state: ParentGraphState,
        name: str,
        subgraph: BaseSubgraph,
        routes_to: str,
    ) -> ParentGraphState:
        logger.info(f"Started running {name}...")
        messages = state["messages"]
        logger.info(f"{name} input messages: {messages}")
        result = await subgraph.run(
            input_message=messages[-1].content if messages else "", next=state["next"]
        )
        logger.info(f"{name} response: {result}")
        return {
            "messages": messages + result["messages"],
            "next": result["next"] if "next" in result else routes_to,
        }

    @staticmethod
    def __call_node_with_chain(
        state: ParentGraphState,
        name: str,
        chain: Runnable[dict[str, list[BaseMessage]], dict[str, str]],
    ) -> ParentGraphState:
        logger.info(f"Started running {name}...")
        messages = state["messages"]
        logger.info(f"{name} input messages: {messages}")
        response = chain.invoke({"messages": messages})
        logger.info(f"{name} response: {response}")
        return {"messages": messages, "next": response["next"]}
