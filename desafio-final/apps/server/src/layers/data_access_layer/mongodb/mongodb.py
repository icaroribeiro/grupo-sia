from typing import AsyncGenerator, Union

from beanie import Document, init_beanie

# from src.layers.business_layer.ai_agents.artificial_intelligence.crews.data_injestion_crew.tools.validate_csv_tool import (
#     ValidateCSVTool,
#     InvoiceValidateCSVTool,
#     InvoiceItemValidateCSVTool,
# )
# from src.layers.business_layer.ai_agents.artificial_intelligence.crews.data_injestion_crew.tools.insert_mongo_tool import (
#     InsertMongoTool,
#     InvoiceInsertMongoTool,
#     InvoiceItemInsertMongoTool,
# )
# from src.layers.data_access_layer.mongodb.repositories.invoice_item_repository import (
#     InvoiceItemRepository,
# )
# from src.layers.data_access_layer.mongodb.repositories.invoice_repository import (
#     InvoiceRepository,
# )
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# from src.layers.business_layer.ai_agents.artificial_intelligence.crews.crew_orchestrator import (
#     CrewOrchestrator,
# )
# from src.layers.business_layer.ai_agents.artificial_intelligence.crews.data_ingestion_crew.data_ingestion_crew import (
#     DataIngestionCrew,
# )
# from src.layers.business_layer.ai_agents.artificial_intelligence.custom_llm import (
#     GeminiFlashLLM,
# )
# from src.layers.business_layer.ai_agents.artificial_intelligence.llms.gpt_mini_llm import (
#     GPTMiniLLM,
# )
from src.layers.core_logic_layer.logging import logger


class MongoDB:
    def __init__(
        self,
        mongodb_params: dict[
            str, Union[str, int, dict[str, Union[str, list[Document]]]]
        ],
    ) -> None:
        self.__client = AsyncIOMotorClient(
            "mongodb://{username}:{password}@{host}:{port}".format(
                username=mongodb_params["username"],
                password=mongodb_params["password"],
                host=mongodb_params["host"],
                port=mongodb_params["port"],
            )
        )

    @property
    async def client(self) -> AsyncGenerator[AsyncIOMotorClient, None]:
        logger.info("Initiating MongoDB client resource...")
        try:
            message = "Success: MongoDB client resource initiated."
            logger.info(message)
            yield self.__client
        except Exception as error:
            message = f"Error: Failed to initiate MongoDB client resource: {error}"
            logger.error(message)
            raise Exception(message)
        finally:
            logger.info("Closing MongoDB client resource...")
            if self.__client:
                self.__client.close()

    async def init_database(
        self, database_name: str, documents: list[Document]
    ) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
        logger.info("Initiating MongoDB database resource and Beanie...")
        database = self.__client[database_name]
        try:
            await init_beanie(
                database=database,
                document_models=documents,
            )
            message = "Success: MongoDB database resource and Beanie initialized."
            logger.info(message)
            yield database
        except Exception as error:
            message = "Error: Failed to initiate MongoDB database resource "
            f"and Beanie: {error}"
            logger.error(message)
            raise Exception(message)
        finally:
            logger.info("Closing MongoDB database resource...")
            if database.client:
                database.client.close()
