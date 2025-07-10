from openai import BaseModel
from pydantic import Field


class UploadFileResponse(BaseModel):
    status: str = Field(default="Uploaded")
