from pydantic import BaseModel


class StreamlitAppErrorDetails(BaseModel):
    message: str
    detail: str | None = None


class StreamlitAppError(Exception):
    def __init__(self, message: str, detail: str | None = None):
        self.error_details = StreamlitAppErrorDetails(
            message=message,
            detail=detail,
        )
        super().__init__(message)
