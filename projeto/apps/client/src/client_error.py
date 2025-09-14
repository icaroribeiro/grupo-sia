from pydantic import BaseModel
from typing import Optional


class ClientErrorDetails(BaseModel):
    message: str
    detail: Optional[str] = None


class ClientError(Exception):
    def __init__(self, message: str, detail: str | None = None):
        self.error_details = ClientErrorDetails(
            message=message,
            detail=detail,
        )
        super().__init__(message)
