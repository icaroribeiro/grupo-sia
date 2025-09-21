# src/workflow.py

from typing import Sequence, TypedDict
import functools
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated
from langgraph.graph import StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.core_logic_layer.settings import ai_settings


class StateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    csv_file_paths: list[str]


def persona_node(
    state: StateModel, name: str, prompt: str, llm_with_tools: Runnable
) -> StateModel:
    messages = state["messages"]
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    agent_chain = prompt_template | llm_with_tools
    response = agent_chain.invoke(messages)

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


workflow = StateGraph(state_schema=StateModel)
llm = LLM(ai_settings=ai_settings)
workflow.add_node(
    node="agent",
    action=functools.partial(
        persona_node,
        name="agent",
        prompt=(
            """
            ROLE:
            - You're an AI agent.
            GOAL:
            - Your primary purpose is to respond any user's question.
            - DO NOT perform any other tasks.
            """
        ),
        llm_with_tools=llm.chat_model.bind_tools(tools=[]),
    ),
)
workflow.set_entry_point("agent")
workflow.set_finish_point("agent")
