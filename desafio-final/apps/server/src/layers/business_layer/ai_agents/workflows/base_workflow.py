from abc import ABC
import functools

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import Runnable

from src.layers.business_layer.ai_agents.models.agent_state import AgentState
from langchain_core.messages import HumanMessage
from abc import abstractmethod
from langgraph.graph import StateGraph


class BaseWorkflow(ABC):
    @abstractmethod
    def create_graph(self, *args, **kwargs) -> StateGraph:
        raise Exception("NotImplementedException")

    def create_supervisor_node() -> AgentState:
        # self.logger.debug("Running supervisor node")
        messages = state["messages"]
        response = supervisor_chain.invoke({"messages": messages})
        # self.logger.debug(f"Supervisor response: {response}")
        return {"messages": messages, "next": response["next"]}

    @staticmethod
    def __supervisor_node(
        state: AgentState,
        prompt: str,
        supervisor_chain: Runnable[BaseMessage, BaseMessage],
    ) -> AgentState:
        response = supervisor_chain.invoke(
            [SystemMessage(content=prompt)] + state["messages"]
        )
        return {"messages": [response]}

    def create_agent_node(
        self,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> None:
        return functools.partial(
            self.__agent_node,
            prompt=prompt,
            llm_with_tools=llm_with_tools,
        )

    # def should_continue(self, state: AgentState) -> str:
    #     messages = state["messages"]
    #     last_message = messages[-1]
    #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
    #         print("Routing to tools node")
    #         return "tools"
    #     print("Routing to END")
    #     return END

    async def run(self, input_message: str) -> dict:
        input_messages = [HumanMessage(content=input_message)]
        result = await self.__graph.ainvoke({"messages": input_messages})
        return result

    @staticmethod
    def __agent_node(
        state: AgentState,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> AgentState:
        response = llm_with_tools.invoke(
            [SystemMessage(content=prompt)] + state["messages"]
        )
        return {"messages": [response]}
