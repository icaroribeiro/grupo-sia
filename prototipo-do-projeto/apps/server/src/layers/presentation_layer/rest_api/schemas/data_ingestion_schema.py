from openai import BaseModel
from pydantic import Field


class DataIngestionResponse(BaseModel):
    status: str = Field(default="Ingested")
