from pydantic import BaseModel


class MealVoucher(BaseModel):
    meal_voucher_value: float
    company_contribution: float
    professional_contribution: float
