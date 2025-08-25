import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.layers.core_logic_layer.logging import logger
from src.server_error import ServerError


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response | ServerError:
        start_time = time.time()
        logger.info("Started logging request...")
        logger.info(f"Request on {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = f"{process_time:.2f}"
            response.headers["X-Process-Time"] = formatted_process_time
            logger.info(
                f"Completed {request.method} {request.url.path} "
                f"with status {response.status_code} "
                f"in {formatted_process_time} ms"
            )
            return response
        except Exception as error:
            message = (
                f"Error: Failed to log request on {request.url.path}: {str(error)}"
            )
            logger.error(message)
            raise ServerError(
                message=message,
                detail=str(error),
            )
