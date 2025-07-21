from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import (
    ai_settings,
    app_settings,
    # mongodb_settings,
)

# from src.layers.data_access_layer.mongodb.documents.invoice_document import (
#     InvoiceDocument,
# )
# from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
#     InvoiceItemDocument,
# )
from src.layers.presentation_layer.rest_api.handlers.api_exception_handler import (
    ExceptionHandler,
)
from src.layers.presentation_layer.rest_api.middlewares.logging_middleware import (
    LoggingMiddleware,
)
from src.layers.presentation_layer.rest_api.routers.v1.router import router as v1_router
from src.server_error import ServerError


class Server:
    _app: FastAPI = FastAPI()

    def __init__(self) -> None:
        self._container = Container()
        self._app.add_middleware(LoggingMiddleware)
        self._app.include_router(router=v1_router, prefix="/api/v1")
        self._app.add_exception_handler(
            HTTPException, ExceptionHandler.http_exception_handler
        )
        self._app.add_exception_handler(
            RequestValidationError, ExceptionHandler.handle_request_validation_error
        )
        self._app.add_exception_handler(
            ServerError, ExceptionHandler.handle_server_error
        )
        self._app.add_event_handler("startup", self.__application_startup_handler)
        self._app.add_event_handler("shutdown", self.__application_shutdown_handler)

    @property
    def app(self) -> FastAPI:
        return self._app

    async def __application_startup_handler(self) -> None:
        logger.info("Application startup initiating...")
        self._container.config.app_settings.from_value(app_settings)
        self._container.config.ai_settings.from_value(ai_settings)
        # self._container.config.mongodb_settings.from_value(mongodb_settings)
        # self._container.config.mongodb_beanie_documents.from_value(
        #     [InvoiceDocument, InvoiceItemDocument]
        # )
        self._container.wire(
            packages=[
                "src.layers.presentation_layer.rest_api.routers.v1",
            ]
        )
        logger.info("Container resources initiating...")
        # await self._container.init_resources()
        logger.info("Application startup complete.")

    async def __application_shutdown_handler(self) -> None:
        logger.info("Application shutdown initiating...")
        # logger.info("Container resources shutting down...")
        # await self._container.shutdown_resources()
        logger.info("Application shutdown complete.")
