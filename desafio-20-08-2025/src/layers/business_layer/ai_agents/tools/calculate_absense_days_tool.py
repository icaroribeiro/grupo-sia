from typing import Type, List
from datetime import datetime

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.business_layer.ai_agents.models.tool_output import Status, ToolOutput
from src.layers.core_logic_layer.logging import logger


class CalculateAbsenseDaysInput(BaseModel):
    date_str: str = Field(
        ...,
        description="",
    )
    working_days: List[int] = Field(
        ...,
        description="A list of integers representing working days.",
    )
    month: int = Field(
        ...,
        description="The month associated with the list of working days (1-12).",
    )


class CalculateAbsenseDaysTool(BaseTool):
    name: str = "calculate_absense_days_tool"
    description: str = (
        "Calculates the number of absense days by counting how many working days in a "
        "list are smaller than the day part of a given date. The logic is applied "
        "only if the provided month matches the month of the date_str."
    )
    args_schema: Type[BaseModel] = CalculateAbsenseDaysInput

    def _run(self, date_str: str, working_days: List[int], month: int) -> ToolOutput:
        logger.info(f"Calling {self.name}...")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month_of_date_str = date_obj.month
            day_of_month = date_obj.day

            if month != month_of_date_str:
                return ToolOutput(
                    status=Status.SUCCEED,
                    result=None,
                )

            absense_days = sum(1 for day in working_days if day < day_of_month)

            return ToolOutput(
                status=Status.SUCCEED,
                result=absense_days,
            )
        except Exception as error:
            message = f"Error during absense days calculation: {str(error)}"
            logger.error(message)
            return ToolOutput(status=Status.FAILED, result=message)

    async def _arun(
        self, date_str: str, working_days: List[int], month: int
    ) -> ToolOutput:
        return self._run(date_str, working_days, month)
