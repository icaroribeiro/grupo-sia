from typing import Type, List
from datetime import datetime
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from src.layers.core_logic_layer.logging import logger
from langchain_core.messages import ToolMessage
from typing import Annotated


from langchain_core.tools import InjectedToolCallId


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
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class CalculateAbsenseDaysTool(BaseTool):
    name: str = "calculate_absense_days_tool"
    description: str = """
    Calculates the number of absence days by counting how many working days in the
    list associated with the specified syndicate name and the month from the given date
    are smaller than the day part of the date.
    Returns the number of absense days.
    """
    args_schema: Type[BaseModel] = CalculateAbsenseDaysInput

    def _run(
        self,
        date_str: str,
        working_days_by_syndicate_name: dict[str, dict[int, List[int]]],
        syndicate_name: str,
        tool_call_id: str,
    ) -> ToolMessage:
        logger.info(f"Calling {self.name} with syndicate_name: {syndicate_name}...")
        try:
            if syndicate_name not in working_days_by_syndicate_name:
                message = f"Syndicate name '{syndicate_name}' not found in working_days_by_syndicate_name"
                logger.error(message)
                return ToolMessage(
                    content="absense_days:0",
                    name=self.name,
                    tool_call_id=tool_call_id,
                )

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
            day_of_month = date_obj.day

            if month not in working_days_by_syndicate_name[syndicate_name]:
                message = f"Month {month} not found for syndicate '{syndicate_name}'"
                logger.error(message)
                return ToolMessage(
                    content="absense_days:0",
                    name=self.name,
                    tool_call_id=tool_call_id,
                )

            working_days = working_days_by_syndicate_name[syndicate_name][month]
            absense_days = sum(1 for day in working_days if day < day_of_month)

            return ToolMessage(
                content=f"absense_days:{absense_days}",
                name=self.name,
                tool_call_id=tool_call_id,
            )
        except Exception as error:
            message = f"Error during absence days calculation: {str(error)}"
            logger.error(message)
            return ToolMessage(
                content="absense_days:0",
                name=self.name,
                tool_call_id=tool_call_id,
            )

    async def _arun(
        self,
        date_str: str,
        working_days_by_syndicate_name: dict[str, dict[int, List[int]]],
        syndicate_name: str,
        tool_call_id: str,
    ) -> ToolMessage:
        return self._run(
            date_str=date_str,
            working_days_by_syndicate_name=working_days_by_syndicate_name,
            syndicate_name=syndicate_name,
            tool_call_id=tool_call_id,
        )
