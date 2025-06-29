from fastapi import FastAPI
from urllib.parse import quote

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.settings.mongodb_settings import (
    get_mongodb_settings,
)
from src.layers.presentation_layer.routers.v1.v1_router import v1_router
from src.layers.core_logic_layer.logging import logger


class Server:
    __app: FastAPI = FastAPI()

    def __init__(self):
        self.__container = Container()
        self.__app.include_router(router=v1_router, prefix="/api/v1")
        self.__app.add_event_handler("startup", self.__application_startup_handler)
        self.__app.add_event_handler("shutdown", self.__application_shutdown_handler)

    def get_app(self) -> FastAPI:
        return self.__app

    async def __application_startup_handler(self) -> None:
        logger.info("Application startup initiating...")
        mongodb_uri_template = "mongodb://{username}:{password}@{host}:{port}"
        mongo_database_settings = get_mongodb_settings()
        mongodb_uri = mongodb_uri_template.format(
            username=quote(mongo_database_settings.username),
            password=quote(mongo_database_settings.password),
            host=mongo_database_settings.host,
            port=mongo_database_settings.port,
        )
        self.__container.config.mongodb_uri.from_value(mongodb_uri)
        self.__container.config.mongodb_database_name.from_value(
            mongo_database_settings.database
        )
        self.__container.wire(
            packages=[
                "src.layers.presentation_layer.routers.v1",
            ]
        )
        logger.info("Initializing container resources...")
        await self.__container.init_resources()
        logger.info("Application startup complete.")

    async def __application_shutdown_handler(self) -> None:
        logger.info("Application shutdown initiating...")
        await self.__container.shutdown_resources()
        logger.info("Application shutdown complete.")
