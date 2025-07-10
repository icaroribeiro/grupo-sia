import time

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.layers.core_logic_layer.logging import logger
from src.server_error import ServerError


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Started {request.method} {request.url.path}")

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
                f"Got an error when logging request on {request.url.path}: {str(error)}"
            )
            logger.error(message)
            raise ServerError(
                message=message,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(error),
            )
