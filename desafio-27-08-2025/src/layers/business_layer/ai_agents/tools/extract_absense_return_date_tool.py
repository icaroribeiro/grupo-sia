import re
from datetime import datetime
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.business_layer.ai_agents.models.tool_output import Status, ToolOutput
from src.layers.core_logic_layer.logging import logger


class ExtractAbsenseReturnDateInput(BaseModel):
    detail: str = Field(
        ...,
        description="A string containing an embedded date in 'DD/MM' format. (e.g., `retorno de férias + licença em DD/MM`)",
    )


class ExtractAbsenseReturnDateTool(BaseTool):
    name: str = "extract_absense_return_date_tool"
    description: str = "Extracts and validates a date in `DD/MM` format from a string and returns it in `YYYY-MM-DD` format, assuming the year is 2025."
    args_schema: Type[BaseModel] = ExtractAbsenseReturnDateInput

    def _run(self, detail: str) -> ToolOutput:
        logger.info(f"Calling {self.name}...")
        try:
            if not isinstance(detail, str):
                return ToolOutput(
                    status=Status.FAILED,
                    result="Input must be a string.",
                )

            match = re.search(r"\b(\d{2}/\d{2})\b", detail)
            if not match:
                return ToolOutput(
                    status=Status.FAILED,
                    result="No 'DD/MM' date found in the string.",
                )

            date_part = match.group(1)
            day, month = map(int, date_part.split("/"))

            if not (1 <= day <= 31 and 1 <= month <= 12):
                return ToolOutput(
                    status=Status.FAILED,
                    result="Invalid day or month value.",
                )

            formatted_date = datetime.strptime(
                f"2025-{month:02d}-{day:02d}", "%Y-%m-%d"
            ).strftime("%Y-%m-%d")

            return ToolOutput(
                status=Status.SUCCEED,
                result=formatted_date,
            )
        except Exception as error:
            message = f"Error during date extraction: {str(error)}"
            logger.error(message)
            return ToolOutput(status=Status.FAILED, result=message)

    async def _arun(self, date_str: str) -> ToolOutput:
        return self._run(date_str)
