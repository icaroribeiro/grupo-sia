from typing import Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput


class SharedWorkflowStateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    task_description: str
    tool_output: ToolOutput
