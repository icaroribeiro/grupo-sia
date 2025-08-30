from typing import Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class DataIngestionStateModel(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    csv_file_paths: list[str] | None = None
    ingestion_args: list[dict[str, str]] | None = None
