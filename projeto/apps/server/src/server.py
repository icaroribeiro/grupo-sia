from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.handlers.api_exception_handler import (
    ExceptionHandler,
)
from src.layers.presentation_layer.rest_api.middlewares.logging_middleware import (
    LoggingMiddleware,
)
from src.layers.presentation_layer.rest_api.routers.v1.router import router as v1_router
from src.server_error import ServerError


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.info("Application startup initiating...")
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutdown initiating...")
    logger.info("Application shutdown complete.")


class Server:
    __APP: FastAPI | None = None

    def __init__(self) -> None:
        self.__APP = FastAPI()
        self.setup_routers()
        self.setup_middlewares()
        self.setup_exception_handlers()

    def setup_routers(self) -> None:
        self.__APP.include_router(router=v1_router, prefix="/api/v1")

    def setup_middlewares(self) -> None:
        self.__APP.add_middleware(LoggingMiddleware)

    def setup_exception_handlers(self) -> None:
        self.__APP.add_exception_handler(
            HTTPException, ExceptionHandler.http_exception_handler
        )
        self.__APP.add_exception_handler(
            RequestValidationError, ExceptionHandler.handle_request_validation_error
        )
        self.__APP.add_exception_handler(
            ServerError, ExceptionHandler.handle_server_error
        )

    @property
    def app(self) -> FastAPI:
        return self.__APP
