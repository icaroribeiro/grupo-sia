from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import (
    ai_settings,
    app_settings,
    mongodb_settings,
)
from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)
from src.layers.presentation_layer.rest_api.handlers.api_exception_handler import (
    ExceptionHandler,
)
from src.layers.presentation_layer.rest_api.middlewares.logging_middleware import (
    LoggingMiddleware,
)
from src.layers.presentation_layer.rest_api.routers.v1.router import router as v1_router
from src.server_error import ServerError


class Server:
    __APP: FastAPI = FastAPI()

    def __init__(self) -> None:
        self.__CONTAINER = Container()
        self.__APP.add_middleware(LoggingMiddleware)
        self.__APP.include_router(router=v1_router, prefix="/api/v1")
        self.__APP.add_exception_handler(
            HTTPException, ExceptionHandler.http_exception_handler
        )
        self.__APP.add_exception_handler(
            RequestValidationError, ExceptionHandler.handle_request_validation_error
        )
        self.__APP.add_exception_handler(
            ServerError, ExceptionHandler.handle_server_error
        )
        self.__APP.add_event_handler("startup", self.__application_startup_handler)
        self.__APP.add_event_handler("shutdown", self.__application_shutdown_handler)

    @property
    def app(self) -> FastAPI:
        return self.__APP

    async def __application_startup_handler(self) -> None:
        logger.info("Application startup initiating...")
        self.__CONTAINER.config.from_dict(
            {
                "app_params": {
                    "uploads_data_dir_path": app_settings.uploads_data_dir_path
                }
            }
        )

        self.__CONTAINER.config.from_dict(
            {
                "llm_params": {
                    "provider": ai_settings.llm_provider,
                    "model": ai_settings.llm_model,
                    "temperature": ai_settings.llm_temperature,
                    "api_key": ai_settings.llm_api_key,
                }
            }
        )

        self.__CONTAINER.config.from_dict(
            {
                "mongodb_params": {
                    "username": quote(mongodb_settings.username),
                    "password": quote(mongodb_settings.password),
                    "host": mongodb_settings.host,
                    "port": mongodb_settings.port,
                    "database": {
                        "name": mongodb_settings.database,
                        "documents": [InvoiceDocument, InvoiceItemDocument],
                    },
                }
            }
        )

        self.__CONTAINER.wire(
            packages=[
                "src.layers.presentation_layer.rest_api.routers.v1",
            ]
        )

        logger.info("Initiating container resources...")
        await self.__CONTAINER.init_resources()
        logger.info("Application startup complete.")

    async def __application_shutdown_handler(self) -> None:
        logger.info("Application shutdown initiating...")
        await self.__CONTAINER.shutdown_resources()
        logger.info("Application shutdown complete.")
