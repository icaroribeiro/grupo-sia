from typing import AsyncGenerator

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from apps.server.src.layers.core_logic_layer.settings.postgresdb_settings import (
    PostgresDBSettings,
)
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.mongodb_settings import MongoDBSettings


class PostgresDB:
    def __init__(
        self,
        postgresdb_settings: PostgresDBSettings,
    ) -> None:
        self.__session = self.__create_session(postgresdb_settings=postgresdb_settings)

    @property
    async def client(self) -> AsyncGenerator[AsyncIOMotorClient, None]:
        logger.info("MongoDB client startup initiating...")
        try:
            message = "Success: MongoDB client startup complete."
            logger.info(message)
            yield self.__client
        except Exception as error:
            message = f"Error: Failed to initiate MongoDB client: {error}"
            logger.error(message)
            raise Exception(message)
        finally:
            logger.info("MongoDB client close initiating...")
            if self.__client:
                self.__client.close()
                logger.info("MongoDB client close complete.")

    async def init_database(
        self, database_name: str, documents: list[Document]
    ) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
        logger.info("MongoDB database and Beanie startup initiating...")
        database = self.__client[database_name]
        try:
            await init_beanie(
                database=database,
                document_models=documents,
            )
            message = "Success: MongoDB database and Beanie startup complete."
            logger.info(message)
            yield database
        except Exception as error:
            message = f"Error: Failed to initiate MongoDB database and Beanie: {error}"
            logger.error(message)
            raise Exception(message)
        finally:
            logger.info("MongoDB database close initiating...")
            if database.client:
                database.client.close()
                logger.info("MongoDB database close complete.")

    @staticmethod
    def __create_client(mongodb_settings: MongoDBSettings) -> AsyncIOMotorClient:
        return create_async_engine(
            "mongodb://{username}:{password}@{host}:{port}".format(
                username=mongodb_settings.username,
                password=mongodb_settings.password,
                host=mongodb_settings.host,
                port=mongodb_settings.port,
            )
        )
