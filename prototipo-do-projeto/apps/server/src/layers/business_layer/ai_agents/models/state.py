from typing import Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class ParentGraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str


class SubgraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str
