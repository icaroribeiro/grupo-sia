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
