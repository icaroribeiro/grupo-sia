from pydantic import BaseModel, Field


class HealthcheckResponse(BaseModel):
    status: str = Field(default="Healthy")
