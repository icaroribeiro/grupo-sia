from typing import TypedDict
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class DataIngestionStateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    ingestion_args_list: list[dict[str, str]]
