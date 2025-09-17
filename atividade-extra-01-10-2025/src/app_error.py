from pydantic import BaseModel


class AppErrorDetails(BaseModel):
    message: str
    detail: str | None = None


class AppError(Exception):
    def __init__(self, message: str, detail: str | None = None):
        self.error_details = AppErrorDetails(
            message=message,
            detail=detail,
        )
        super().__init__(message)
