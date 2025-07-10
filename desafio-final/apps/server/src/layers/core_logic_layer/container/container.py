from typing import AsyncGenerator

from beanie import init_beanie
from dependency_injector import containers, providers

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
from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    async def mongodb_client(
        config: providers.Configuration,
    ) -> AsyncGenerator[AsyncIOMotorClient]:
        logger.info("Initiating MongoDB client resource...")
        client = AsyncIOMotorClient(
            config["mongodb"]["uri"],
        )
        try:
            await client["admin"].command("ping")
            logger.info("MongoDB client resource initialized successfully.")
            yield client
        except Exception as error:
            logger.error(
                f"Got an error when initiating MongoDB client resource: {error}"
            )
            raise
        finally:
            logger.info("Closing MongoDB client resource...")
            if client:
                client.close()

    async def mongodb_database(
        client: AsyncIOMotorClient,
        config: providers.Configuration,
    ) -> AsyncGenerator[AsyncIOMotorDatabase]:
        logger.info("Initiating MongoDB database resource and Beanie...")
        database = client[config["mongodb"]["database"]]
        try:
            await init_beanie(
                database=database,
                document_models=[
                    InvoiceDocument,
                    InvoiceItemDocument,
                ],
            )
            logger.info(
                "MongoDB database resource and Beanie initialized successfully."
            )
            yield database
        except Exception as error:
            logger.error(
                f"Got an error when initiating MongoDB database resource and Beanie: {error}"
            )
            raise
        finally:
            logger.info("Closing MongoDB database resource...")
            if database.client:
                database.client.close()

    mongodb_client_resource = providers.Resource(mongodb_client, config=config)

    mongodb_database_resource = providers.Resource(
        mongodb_database, client=mongodb_client_resource, config=config
    )

    # async def llm(config: providers.Configuration) -> LLM:
    #     logger.info("Initiating LLM...")
    #     llm_name = config["llm"]
    #     openai_api_key = config["openai_api_key"]
    #     gemini_api_key = config["gemini_api_key"]
    #     temperature = config["temperature"]

    #     if llm_name.lower() not in ["gpt", "gemini"]:
    #         message = (
    #             "LLM not configured. "
    #             + "You must set up a LLM in your .env file or environment variables."
    #         )
    #         logger.error(message)
    #         raise Exception(message)

    #     llm: LLM
    #     if llm_name.lower() == "gpt":
    #         if not openai_api_key:
    #             message = (
    #                 "OPENAI_API_KEY not configured. "
    #                 + "You must set up an API key in your .env file or environment variables."
    #             )
    #             logger.error(message)
    #             raise Exception(message)
    #         else:
    #             llm = GPTMiniLLM.create(
    #                 temperature=temperature, api_key=openai_api_key
    #             ).llm

    #     if llm_name.lower() == "gemini":
    #         if not gemini_api_key:
    #             message = (
    #                 "GEMINI_API_KEY not configured. "
    #                 + "You must set up an API key in your .env file or environment variables."
    #             )
    #             logger.error(message)
    #             raise Exception(message)
    #         else:
    #             llm = GeminiFlashLLM.create(
    #                 temperature=temperature, api_key=gemini_api_key
    #             ).llm

    #     logger.info("LLM initialized successfully.")
    #     return llm

    # llm_resource = providers.Resource(llm, config=config)

    # data_ingestion_crew = providers.Singleton(DataIngestionCrew, llm=llm_resource)

    # crew_orchestrator = providers.Singleton(
    #     CrewOrchestrator, config=config, data_ingestion_crew=data_ingestion_crew
    # )
