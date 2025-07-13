from typing import Union

from langchain_core.tools import BaseTool

# from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.layers.core_logic_layer.logging import logger


class DisconnectFromMongoDBTool(BaseTool):
    name: str = "disconnect_from_mongodb_tool"
    description: str = """
    Disconnect from MongoDB database.
    
    Args:
        database (AsyncIOMotorDatabase): Motor Database.
    
    Returns:
        Union[str, None]: Status message indicating success or failure
        along with 'None'.
    """

    def _run(self, database: AsyncIOMotorDatabase) -> Union[str, None]:
        logger.info("Started disconnecting from MongoDB...")
        try:
            logger.info("Closing MongoDB client resource...")
            if database.client:
                database.client.close()
            message = "Success: MongoDB client resource closed."
            logger.info(message)
            return (message, None)
        except Exception as error:
            message = f"Error: Failed to disconnect from MongoDB: {error}"
            logger.error(message)
            return (message, None)
