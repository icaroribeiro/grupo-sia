from openai import BaseModel
from pydantic import Field


class DatabaseIngestionResponse(BaseModel):
    status: str = Field(default="Ingested")
