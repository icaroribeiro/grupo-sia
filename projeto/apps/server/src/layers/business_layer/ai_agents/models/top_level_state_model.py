from typing import TypedDict
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class TopLevelStateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_team: str
    # task_description: str
