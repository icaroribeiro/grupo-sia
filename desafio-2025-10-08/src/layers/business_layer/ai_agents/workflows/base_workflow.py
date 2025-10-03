import re
from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph

from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent
from src.layers.business_layer.ai_agents.models.base_state_graph_model import (
    BaseStateGraphModel,
)
from src.layers.business_layer.ai_agents.models.base_state_model import BaseStateModel
from src.layers.business_layer.ai_agents.models.data_analysis_state_model import (
    DataAnalysisStateModel,
)
from src.layers.core_logic_layer.logging import logger


class BaseWorkflow(ABC):
    def __init__(self) -> None:
        self.name: str = ""
        self._workflow: Optional[BaseStateGraphModel] = None

    @property
    def workflow(self) -> StateGraph:
        if self._workflow is None:
            self._workflow = self._build_workflow()
        return self._workflow.graph

    @abstractmethod
    def _build_workflow(self) -> BaseStateGraphModel:
        pass

    @staticmethod
    def agent_node(
        state: BaseStateModel,
        agent: BaseAgent,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> DataAnalysisStateModel:
        logger.info(f"Calling {agent.name}...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", agent.prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        agent_chain = prompt_template | llm_with_tools
        response = agent_chain.invoke(messages)
        # logger.info(f"{name} response: {response}")

        # It's to deduplicate tool calls before updating the state by ensuring that
        # only unique tool calls (based on name and arguments) are passed to
        # the tools node.
        if hasattr(response, "tool_calls") and response.tool_calls:
            seen = set()
            unique_tool_calls = []
            for tool_call in response.tool_calls:
                tool_key = (tool_call["name"], str(tool_call["args"]))
                if tool_key not in seen:
                    seen.add(tool_key)
                    unique_tool_calls.append(tool_call)
            response.tool_calls = unique_tool_calls

        return {"messages": messages + [response]}

    @staticmethod
    def handoff_node(
        state: BaseStateModel,
    ) -> BaseStateModel:
        logger.info("Calling handoff by supervisor...")
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        pattern = r"transfer_to_agent=(\w+)::task=(.+)"
        match = re.search(pattern, last_message.content)
        if match:
            agent_name = match.group(1)
            task_description = match.group(2)
            # logger.info(f"Parsed agent: {agent_name}, task= {task_description}")
            new_task_message = HumanMessage(content=task_description)
            return {
                "messages": state["messages"] + [new_task_message],
                "next_agent": agent_name,
            }
        logger.warning("No valid agent transfer found in handoff_node")
        return {"messages": state["messages"], "next_agent": "supervisor_agent"}

    @staticmethod
    def route_supervisor(
        state: BaseStateModel,
        name: str,
    ) -> str:
        logger.info(f"Routing from {name}...")
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "supervisor_agent_tools"
        else:
            routes_to = END
        logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def route_agent(
        state: BaseStateModel,
        name: str,
        routes_to_by_tool_name: dict[str, str] | None,
    ) -> str:
        logger.info(f"Routing from {name}...")
        last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            if routes_to_by_tool_name:
                first_tool_name = last_message.tool_calls[0].get(
                    "name"
                ) or last_message.tool_calls[0].get("function", {}).get("name")
                routes_to = routes_to_by_tool_name.get(first_tool_name, "tools")
            else:
                routes_to = "tools"
        else:
            routes_to = "supervisor_agent"
        logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def route_handoff(state: BaseStateModel) -> str:
        logger.info("Routing from handoff by supervisor...")
        # last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        next_agent = state.get("next_agent", "supervisor_agent")
        logger.info(f"To {next_agent}...")
        return next_agent
