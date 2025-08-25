from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.layers.core_logic_layer.logging import logger
from src.server_error import ServerError


class ExceptionHandler:
    @staticmethod
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        message = (
            f"Error: HTTPException in {request.method} {request.url.path}: "
            f"status_code={exc.status_code}, detail={exc.detail}"
        )
        logger.error(message)
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @staticmethod
    async def handle_request_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        message = (
            f"Error: ValidationError in {request.method} {request.url.path}: "
            f"detail={str(error.errors())}"
        )
        logger.error(message)
        return JSONResponse(
            content=ServerError(
                message="Error: Validation failed",
                status_code=status_code,
                detail=str(error.errors()),
            ).error_details.model_dump(),
            status_code=status_code,
        )

    @staticmethod
    async def handle_server_error(request: Request, error: ServerError) -> JSONResponse:
        message = (
            f"Error: ServerError in {request.method} {request.url.path}: "
            f"status_code={error.status_code}, detail={error.error_details.detail}"
        )
        logger.error(message)
        return JSONResponse(
            content=error.error_details.model_dump(),
            status_code=error.status_code,
        )
