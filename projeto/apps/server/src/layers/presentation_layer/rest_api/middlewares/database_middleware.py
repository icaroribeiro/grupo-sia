import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.layers.core_logic_layer.logging import logger
from src.server_error import ServerError


class DatabaseMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    @inject
    async def dispatch(self, request: Request, call_next, session: AsyncSession = Depends(Container.async.session)) -> Response | ServerError:
        async with session as db_session:
            try:
                response = await call_next(request)
                if response.status_code == 200:
                    await db_session.commit()
                logger.info(
                    f"Completed {request.method} {request.url.path} "
                    f"with status {response.status_code} "
                    f"in {formatted_process_time} ms"
                )
                return response
            except Exception as error:
                await db_session.rollback()
                message = (
                    f"Error: Failed to log request on {request.url.path}: {str(error)}"
                )
                logger.error(message)
                raise ServerError(
                    message=message,
                    detail=str(error),
                )
            finally:
                await db_session.close()
