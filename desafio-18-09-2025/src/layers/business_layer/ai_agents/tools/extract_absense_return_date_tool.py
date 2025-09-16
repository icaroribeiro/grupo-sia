import re
from datetime import datetime
from typing import Annotated, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from langchain_core.messages import ToolMessage
from src.layers.core_logic_layer.logging import logger
from langchain_core.tools import InjectedToolCallId


class ExtractAbsenseReturnDateInput(BaseModel):
    detail: str = Field(
        ...,
        description="A string containing an embedded date in 'DD/MM' format. (e.g., `retorno de férias + licença em DD/MM`)",
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class ExtractAbsenseReturnDateTool(BaseTool):
    name: str = "extract_absense_return_date_tool"
    description: str = """
    Extracts and validates a date in `DD/MM` format from a string.
    Returns the date in `YYYY-MM-DD` format, assuming the year is 2025.
    """
    args_schema: Type[BaseModel] = ExtractAbsenseReturnDateInput

    def _run(self, detail: str, tool_call_id: str) -> ToolMessage:
        logger.info(f"Calling {self.name}...")
        try:
            if not isinstance(detail, str):
                message = "Error during date extraction: Input must be a string."
                logger.error(message)
                return ToolMessage(
                    content="return_date:",
                    name=self.name,
                    tool_call_id=tool_call_id,
                )

            match = re.search(r"\b(\d{2}/\d{2})\b", detail)
            if not match:
                message = (
                    "Error during date extraction: No 'DD/MM' date found in the string."
                )
                logger.error(message)
                return ToolMessage(
                    content="return_date:",
                    name=self.name,
                    tool_call_id=tool_call_id,
                )

            date_part = match.group(1)
            day, month = map(int, date_part.split("/"))

            if not (1 <= day <= 31 and 1 <= month <= 12):
                message = "Error during date extraction: Invalid day or month value."
                logger.error(message)
                return ToolMessage(
                    content="return_date:",
                    name=self.name,
                    tool_call_id=tool_call_id,
                )

            formatted_date = datetime.strptime(
                f"2025-{month:02d}-{day:02d}", "%Y-%m-%d"
            ).strftime("%Y-%m-%d")
            return ToolMessage(
                content=f"return_date:{formatted_date}",
                name=self.name,
                tool_call_id=tool_call_id,
            )
        except Exception as error:
            message = f"Error during date extraction: {str(error)}"
            logger.error(message)
            return ToolMessage(
                content="return_date:",
                name=self.name,
                tool_call_id=tool_call_id,
            )

    async def _arun(self, date_str: str, tool_call_id: str) -> ToolMessage:
        return self._run(date_str=date_str, tool_call_id=tool_call_id)
