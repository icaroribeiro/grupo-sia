from typing import Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class DataAnalysisStateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    csv_file_paths: list[str]
