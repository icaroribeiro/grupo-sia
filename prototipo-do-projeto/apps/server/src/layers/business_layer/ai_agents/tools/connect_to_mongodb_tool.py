from typing import Union

from beanie import Document, init_beanie
from langchain_core.tools import BaseTool
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.layers.core_logic_layer.logging import logger


class ConnectToMongoDBTool(BaseTool):
    name: str = "connect_to_mongodb_tool"
    description: str = """
    Connect to MongoDB database.
    
    Args:
        uri (str): MongoDB URI.
        database_name (str): MongoDB database name.
        documents (list[Document]): List of Beanie document classes.
    
    Returns:
        Union[str, AsyncIOMotorDatabase | None]: Status message indicating success or
        failure along with Motor Database on success or 'None' on failure.
    """

    async def _arun(
        self, uri: str, database_name: str, documents: list[Document]
    ) -> Union[str, AsyncIOMotorDatabase | None]:
        logger.info("Started connecting to MongoDB...")
        logger.info("Initiating MongoDB client resource...")
        client = AsyncIOMotorClient(uri)
        try:
            await client["admin"].command("ping")
            message = "Success: MongoDB client resource initiated."
            logger.info(message)
        except Exception as error:
            message = f"Error: Failed to initiate MongoDB client resource: {error}"
            logger.error(message)
            return (message, None)

        logger.info("Initiating MongoDB database resource and Beanie...")
        database = client[database_name]
        try:
            await init_beanie(
                database=database,
                document_models=documents,
            )
            message = "Success: MongoDB database resource and Beanie initialized."
            logger.info(message)
            return (message, database)
        except Exception as error:
            message = "Error: Failed to initiate MongoDB database resource "
            f"and Beanie: {error}"
            logger.error(message)
            return (message, None)

    def _run(self, *args, **kwargs) -> str:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
