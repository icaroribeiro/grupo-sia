from openai import BaseModel


class SendGeneralQueryRequest(BaseModel):
    query: str


class SendGeneralQueryResponse(BaseModel):
    answer: str


class SendTechnicalQueryRequest(BaseModel):
    query: str
    format_instructions_dict: dict | None = None


class SendTechnicalQueryResponse(BaseModel):
    answer: dict
