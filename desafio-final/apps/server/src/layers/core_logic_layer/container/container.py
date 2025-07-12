from beanie import Document
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
from src.layers.core_logic_layer.llm.llm import LLM
from src.layers.data_access_layer.mongodb.mongodb import MongoDB
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    mongodb = providers.Singleton(MongoDB, mongodb_params=config.mongodb_params)

    async def init_mongodb_client(
        mongodb: providers.Singleton,
    ) -> AsyncGenerator[AsyncIOMotorClient, None]:
        async for client in mongodb.client:
            yield client

    mongodb_client_resource = providers.Resource(
        init_mongodb_client,
        mongodb=mongodb,
    )

    async def init_mongodb_database(
        mongodb: providers.Singleton, database_name: str, documents: list[Document]
    ) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
        async for database in mongodb.init_database(
            database_name=database_name, documents=documents
        ):
            yield database

    mongodb_database_resource = providers.Resource(
        init_mongodb_database,
        mongodb=mongodb,
        database_name=config.mongodb_params.database.name,
        documents=config.mongodb_params.database.documents,
    )

    llm = providers.Singleton(LLM, llm_params=config.llm_params)

    # async def mongodb_client(
    #     config: providers.Configuration,
    # ) -> AsyncGenerator[AsyncIOMotorClient]:
    #     logger.info("Initiating MongoDB client resource...")
    #     client = AsyncIOMotorClient(
    #         config["mongodb_params"]["uri"],
    #     )
    #     try:
    #         await client["admin"].command("ping")
    #         message = "Success: MongoDB client resource initiated."
    #         logger.info(message)
    #         yield client
    #     except Exception as error:
    #         message = f"Error: Failed to initiate MongoDB client resource: {error}"
    #         logger.error(message)
    #         raise Exception(message)
    #     finally:
    #         logger.info("Closing MongoDB client resource...")
    #         if client:
    #             client.close()

    # async def mongodb_database(
    #     client: AsyncIOMotorClient,
    #     config: providers.Configuration,
    # ) -> AsyncGenerator[AsyncIOMotorDatabase]:
    #     logger.info("Initiating MongoDB database resource and Beanie...")
    #     database = client[config["mongodb_params"]["database_name"]]
    #     try:
    #         await init_beanie(
    #             database=database,
    #             document_models=[
    #                 InvoiceDocument,
    #                 InvoiceItemDocument,
    #             ],
    #         )
    #         message = "Success: MongoDB database resource and Beanie initialized."
    #         logger.info(message)
    #         yield database
    #     except Exception as error:
    #         message = "Error: Failed to initiate MongoDB database resource "
    #         f"and Beanie: {error}"
    #         logger.error(message)
    #         raise Exception(message)
    #     finally:
    #         logger.info("Closing MongoDB database resource...")
    #         if database.client:
    #             database.client.close()

    # mongodb_client_resource = providers.Resource(mongodb_client, config=config)

    # mongodb_database_resource = providers.Resource(
    #     mongodb_database, client=mongodb_client_resource, config=config
    # )

    # mongodb_resource = providers.Resource(mongodb, config=config)

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
