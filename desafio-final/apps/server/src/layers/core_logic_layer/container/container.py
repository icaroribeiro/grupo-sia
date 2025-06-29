from typing import AsyncGenerator
from beanie import init_beanie
from dependency_injector import containers, providers
from src.layers.core_logic_layer.logging import logger

# from src.layers.core_logic_layer.ai.crews.data_injestion_crew.tools.validate_csv_tool import (
#     ValidateCSVTool,
#     InvoiceValidateCSVTool,
#     InvoiceItemValidateCSVTool,
# )
# from src.layers.core_logic_layer.ai.crews.data_injestion_crew.tools.insert_mongo_tool import (
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
        logger.info("Initializing MongoDB client resource...")
        client = AsyncIOMotorClient(
            config["mongodb_uri"],
        )
        try:
            await client["admin"].command("ping")
            logger.info("MongoDB client resource initialized successfully.")
            yield client
        except Exception as error:
            logger.error(
                f"Got an error when initializing MongoDB client resource: {error}"
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
        logger.info("Initializing MongoDB database resource and Beanie...")
        database = client[config["mongodb_database_name"]]
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
                f"Got an error when initializing MongoDB database resource and Beanie: {error}"
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

    # invoice_csv_validation_tool = providers.Factory(InvoiceValidateCSVTool)

    # invoice_item_csv_validation_tool = providers.Factory(InvoiceItemValidateCSVTool)

    # csv_validation_tool = providers.Factory(
    #     ValidateCSVTool,
    #     tools=providers.List(
    #         invoice_csv_validation_tool, invoice_item_csv_validation_tool
    #     ),
    # )

    # invoice_repository = providers.Factory(InvoiceRepository)

    # invoice_item_repository = providers.Factory(InvoiceItemRepository)

    # invoice_insert_mongo_tool = providers.Factory(
    #     InvoiceInsertMongoTool, repository=invoice_repository
    # )

    # invoice_item_insert_mongo_tool = providers.Factory(
    #     InvoiceItemInsertMongoTool, repository=invoice_item_repository
    # )

    # insert_mongo_tool = providers.Factory(
    #     InsertMongoTool,
    #     tools=providers.List(invoice_insert_mongo_tool, invoice_item_insert_mongo_tool),
    # )
