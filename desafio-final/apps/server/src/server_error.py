from fastapi import HTTPException, status
from pydantic import BaseModel


class ServerErrorDetails(BaseModel):
    message: str
    details: str | None = None
    is_operational: bool


class ServerError(HTTPException):
    def __init__(
        self, message: str, status_code: int | None = None, detail: str | None = None
    ):
        if status_code is None:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.error_details = ServerErrorDetails(
            message=message,
            is_operational=True if f"{status_code}".startswith("4") else False,
            detail=detail,
        )
        super().__init__(status_code=status_code, detail=detail)
