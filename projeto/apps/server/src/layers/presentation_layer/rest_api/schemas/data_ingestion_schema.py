from typing import Literal
from pydantic import BaseModel, Field


class DataIngestionResponse(BaseModel):
    status: Literal["Ingested", "UnIngested"] = Field(
        ..., description="The status of data ingestion procedure."
    )
