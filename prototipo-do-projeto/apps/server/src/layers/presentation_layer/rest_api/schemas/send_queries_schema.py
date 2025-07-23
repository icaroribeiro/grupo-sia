from openai import BaseModel


class SendQueryRequest(BaseModel):
    query: str


class SendQueryResponse(BaseModel):
    answer: str
