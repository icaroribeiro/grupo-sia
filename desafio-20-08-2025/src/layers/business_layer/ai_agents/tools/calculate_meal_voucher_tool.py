from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.business_layer.ai_agents.models.meal_voucher import MealVoucher
from src.layers.business_layer.ai_agents.models.tool_output import Status, ToolOutput
from src.layers.core_logic_layer.logging import logger


class CalculateMealVoucherInput(BaseModel):
    working_days: int = Field(..., description="Number of an employee's working days.")
    daily_meal_voucher_value: float = Field(
        ..., description="Daily value of the meal voucher."
    )


class CalculateMealVoucherTool(BaseTool):
    name: str = "calculate_meal_voucher_tool"
    description: str = (
        "Calculates meal voucher values based on working days and a daily rate."
    )
    args_schema: Type[BaseModel] = CalculateMealVoucherInput

    def _run(self, working_days: int, daily_meal_voucher_value: float) -> ToolOutput:
        try:
            meal_voucher_value = working_days * daily_meal_voucher_value
            company_contribution = meal_voucher_value * 0.80
            professional_contribution = meal_voucher_value * 0.20

            meal_voucher_data = MealVoucher(
                meal_voucher_value=meal_voucher_value,
                company_contribution=company_contribution,
                professional_contribution=professional_contribution,
            )

            return ToolOutput(status=Status.SUCCEED, result=meal_voucher_data)
        except Exception as error:
            message = f"Error: {str(error)}"
            logger.error(message)
            return ToolOutput(status=Status.FAILED, result=str(error))

    async def _arun(
        self, working_days: int, daily_meal_voucher_value: float
    ) -> ToolOutput:
        return self._run(working_days, daily_meal_voucher_value)
