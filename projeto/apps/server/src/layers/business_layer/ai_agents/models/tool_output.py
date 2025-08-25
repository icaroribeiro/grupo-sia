import ast
from typing import Any
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Status(str, Enum):
    SUCCEED = "succeed"
    FAILED = "failed"


class ToolOutput(BaseModel):
    status: Status = Status.SUCCEED
    result: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_tool_message(cls, content: str) -> "ToolOutput":
        data = dict()
        splitted_parts = content.split()
        for part in splitted_parts:
            key, value = part.split("=", 1)
            if key == "status":
                data[key] = Status(value)
            elif key == "result":
                data[key] = ast.literal_eval(value)
        return cls(**data)
