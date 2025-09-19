from typing import Type, List
from datetime import datetime
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from src.layers.business_layer.ai_agents.models.tool_output import Status, ToolOutput
from src.layers.core_logic_layer.logging import logger


class CalculateAbsenseDaysInput(BaseModel):
    date_str: str = Field(
        ...,
        description="Date in YYYY-MM-DD format to calculate absence days from.",
    )
    working_days_by_syndicate_name: dict[str, dict[int, List[int]]] = Field(
        ...,
        description="Dictionary mapping syndicate names to dictionaries, where each inner dictionary maps months (1-12) to lists of integers representing working days for that month.",
    )
    syndicate_name: str = Field(
        ...,
        description="The syndicate name to select the working days list (e.g., 'SITEPD PR', 'SINDPPD RS', 'SINDPD SP', 'SINDPD RJ').",
    )


class CalculateAbsenseDaysTool(BaseTool):
    name: str = "calculate_absense_days_tool"
    description: str = (
        "Calculates the number of absence days by counting how many working days in the "
        "list associated with the specified syndicate name and the month from the given date "
        "are smaller than the day part of the date. Returns None if the month is not found."
    )
    args_schema: Type[BaseModel] = CalculateAbsenseDaysInput

    def _run(
        self,
        date_str: str,
        working_days_by_syndicate_name: dict[str, dict[int, List[int]]],
        syndicate_name: str,
    ) -> ToolOutput:
        logger.info(f"Calling {self.name} with syndicate_name: {syndicate_name}...")
        try:
            if syndicate_name not in working_days_by_syndicate_name:
                message = f"Syndicate name '{syndicate_name}' not found in working_days_by_syndicate_name"
                logger.error(message)
                return ToolOutput(status=Status.FAILED, result=message)

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
            day_of_month = date_obj.day

            if month not in working_days_by_syndicate_name[syndicate_name]:
                message = f"Month {month} not found for syndicate '{syndicate_name}'"
                logger.error(message)
                return ToolOutput(status=Status.FAILED, result=None)

            working_days = working_days_by_syndicate_name[syndicate_name][month]
            absense_days = sum(1 for day in working_days if day < day_of_month)

            return ToolOutput(
                status=Status.SUCCEED,
                result=absense_days,
            )
        except Exception as error:
            message = f"Error during absence days calculation: {str(error)}"
            logger.error(message)
            return ToolOutput(status=Status.FAILED, result=message)

    async def _arun(
        self,
        date_str: str,
        working_days_by_syndicate_name: dict[str, dict[int, List[int]]],
        syndicate_name: str,
    ) -> ToolOutput:
        return self._run(date_str, working_days_by_syndicate_name, syndicate_name)
