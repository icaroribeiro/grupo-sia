import ast
import re
from typing import Any
from enum import Enum
from pydantic import BaseModel, ConfigDict
import logging

logger = logging.getLogger(__name__)


class Status(str, Enum):
    SUCCEED = "succeed"
    FAILED = "failed"


class ToolOutputModel(BaseModel):
    status: Status = Status.SUCCEED
    result: Any = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_tool_message(cls, content: str) -> "ToolOutputModel":
        data = {}
        # Use regex to find key-value pairs
        status_match = re.search(r"status=(\w+)", content)
        result_match = re.search(r"result=(.+)", content)

        if status_match:
            # Get the string part of the status, e.g., 'succeed'
            status_str = status_match.group(1)
            try:
                data["status"] = Status(status_str)
            except ValueError as e:
                logger.error(f"Invalid status value '{status_str}': {e}")
                data["status"] = Status.FAILED
        else:
            logger.warning("Could not find status in tool message.")
            data["status"] = Status.FAILED

        if result_match:
            result_str = result_match.group(1)
            try:
                # Safely evaluate the result string as a Python literal
                data["result"] = ast.literal_eval(result_str)
            except (ValueError, SyntaxError) as e:
                logger.error(f"Failed to parse result '{result_str}': {e}")
                data["result"] = None
        else:
            data["result"] = None

        return cls(**data)
