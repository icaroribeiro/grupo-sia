from typing import Literal
from pydantic import BaseModel, Field


class HealthcheckResponse(BaseModel):
    status: Literal["Healthy", "UnHealthy"] = Field(
        ..., description="The health status of the REST API."
    )
