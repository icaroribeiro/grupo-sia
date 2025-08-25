from openai import BaseModel


class DataIngestionResponse(BaseModel):
    status: str
