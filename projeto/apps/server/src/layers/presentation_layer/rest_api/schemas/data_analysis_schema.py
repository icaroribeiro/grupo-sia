from typing import Literal
from pydantic import BaseModel, Field


class DataAnalysisRequest(BaseModel):
    question: str
    format_instructions: dict | None = None


class DataAnalysisResponse(BaseModel):
    status: Literal["Analyzed", "UnAnalyzed"] = Field(
        ..., description="The status of the data analysis procedure."
    )
    answer: str | dict | None = Field(
        ..., description="The answer to the user's question."
    )
