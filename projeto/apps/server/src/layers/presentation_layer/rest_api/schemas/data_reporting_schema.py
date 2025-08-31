from openai import BaseModel


class DataReportingRequest(BaseModel):
    question: str
    format_instructions: dict | None = None


class DataReportingResponse(BaseModel):
    answer: str | dict
