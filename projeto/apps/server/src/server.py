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


class Server:
    __APP: FastAPI | None = None

    def __init__(self) -> None:
        self.__APP = FastAPI(
            title="Grupo SIA REST API",
            description="A REST API developed using Python, LangGraph framework and Postgres database.\n\nSome useful links:\n- [The REST API repository](https://github.com/icaroribeiro/grupo-sia/tree/projeto-30-10-2025)",  # noqa: E501
            version="1.0.0",
            contact={
                "name": "Ícaro Ribeiro",
                "email": "icaroribeiro@hotmail.com",
                "url": "https://github.com/icaroribeiro",
            },
            license_info={
                "name": "MIT",
            },
            openapi_tags=[
                {
                    "name": "healthcheck",
                    "description": "Everything about health check",
                },
                {
                    "name": "data-ingestion",
                    "description": "Everything about data ingestion",
                },
                {
                    "name": "data-analysis",
                    "description": "Everything about data analysis",
                },
            ],
            servers=[
                {
                    "url": "http://localhost:8000",
                    "description": "Production environment",
                },
            ],
        )
        self.setup_routers()
        self.setup_middlewares()
        self.setup_exception_handlers()
        self.setup_event_handlers()

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

    def setup_event_handlers(self) -> None:
        self.__APP.add_event_handler("startup", self.__startup_handler)
        self.__APP.add_event_handler("shutdown", self.__shutdown_handler)

    async def __startup_handler(self) -> None:
        logger.info("Server startup initiating...")
        logger.info("Server startup complete.")

    async def __shutdown_handler(self) -> None:
        logger.info("Server shutdown initiating...")
        logger.info("Server shutdown complete.")

    @property
    def app(self) -> FastAPI:
        return self.__APP
