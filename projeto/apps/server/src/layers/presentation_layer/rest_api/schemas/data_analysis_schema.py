from openai import BaseModel


class DataAnalysisRequest(BaseModel):
    question: str
    format_instructions: dict | None = None


class DataAnalysisResponse(BaseModel):
    answer: str | dict
