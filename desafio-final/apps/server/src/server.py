from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.layers.core_logic_layer.settings.mongodb_settings import (
    MongoDBSettings,
)
from src.layers.core_logic_layer.settings.settings import Settings
from src.layers.presentation_layer.rest_api.handlers.api_exception_handler import (
    ExceptionHandler,
)
from src.layers.presentation_layer.rest_api.middlewares.logging_middleware import (
    LoggingMiddleware,
)
from src.layers.presentation_layer.rest_api.routers.v1.router import router as v1_router
from src.server_error import ServerError


class Server:
    __app: FastAPI = FastAPI()
    __container: Container = Container()

    def __init__(self) -> None:
        self.__app.add_middleware(LoggingMiddleware)
        self.__app.include_router(router=v1_router, prefix="/api/v1")
        self.__app.add_exception_handler(
            HTTPException, ExceptionHandler.http_exception_handler
        )
        self.__app.add_exception_handler(
            RequestValidationError, ExceptionHandler.handle_request_validation_error
        )
        self.__app.add_exception_handler(
            ServerError, ExceptionHandler.handle_server_error
        )
        self.__app.add_event_handler("startup", self.__application_startup_handler)
        self.__app.add_event_handler("shutdown", self.__application_shutdown_handler)

    def get_app(self) -> FastAPI:
        return self.__app

    async def __application_startup_handler(self) -> None:
        logger.info("Application startup initiating...")
        settings = Settings()
        self.__container.config.from_dict(
            {"app": {"uploads_data_dir_path": settings.uploads_data_dir_path}}
        )

        ai_settings = AISettings()
        self.__container.config.from_dict(
            {
                "llm": {
                    "provider": ai_settings.llm_provider,
                    "model": ai_settings.llm_model,
                    "temperature": ai_settings.llm_temperature,
                    "api_key": ai_settings.llm_api_key,
                }
            }
        )

        mongodb_uri_template = "mongodb://{username}:{password}@{host}:{port}"
        mongodb_settings = MongoDBSettings()
        mongodb_uri = mongodb_uri_template.format(
            username=quote(mongodb_settings.username),
            password=quote(mongodb_settings.password),
            host=mongodb_settings.host,
            port=mongodb_settings.port,
        )
        self.__container.config.from_dict(
            {
                "mongodb": {
                    "uri": mongodb_uri,
                    "database": mongodb_settings.database,
                }
            }
        )

        self.__container.wire(
            packages=[
                "src.layers.presentation_layer.rest_api.routers.v1",
            ]
        )
        logger.info("Initiating container resources...")
        await self.__container.init_resources()
        logger.info("Application startup complete.")

    async def __application_shutdown_handler(self) -> None:
        logger.info("Application shutdown initiating...")
        await self.__container.shutdown_resources()
        logger.info("Application shutdown complete.")
