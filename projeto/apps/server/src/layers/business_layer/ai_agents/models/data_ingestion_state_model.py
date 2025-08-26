from typing import Any, TypedDict, List
from langchain_core.messages import BaseMessage


class DataIngestionStateModel(TypedDict):
    messages: List[BaseMessage]
    task_description: str
    tool_output_result: Any
