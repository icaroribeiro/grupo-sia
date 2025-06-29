import asyncio
import os
from urllib.parse import quote

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.layers.core_logic_layer.settings.mongodb_settings import (
    get_mongodb_settings,
)
from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)
from src.layers.core_logic_layer.logging import logger


async def main() -> None:
    logger.info("Initializing MongoDB...")
    mongodb_uri_template = "mongodb://{username}:{password}@{host}:{port}"
    mongo_database_settings = get_mongodb_settings()
    mongodb_uri = mongodb_uri_template.format(
        username=quote(mongo_database_settings.username),
        password=quote(mongo_database_settings.password),
        host=mongo_database_settings.host,
        port=mongo_database_settings.port,
    )

    logger.info("Initializing MongoDB client resource...")
    client = AsyncIOMotorClient(mongodb_uri)
    try:
        await client["admin"].command("ping")
        logger.info("MongoDB client resource initialized successfully.")
    except Exception as error:
        logger.error(f"Got an error when initializing MongoDB client resource: {error}")
        raise

    logger.info("Initializing MongoDB database resource and Beanie...")
    database = client[mongo_database_settings.database]
    try:
        await init_beanie(
            database=database,
            document_models=[
                InvoiceDocument,
                InvoiceItemDocument,
            ],
        )
        logger.info("MongoDB database resource and Beanie initialized successfully.")
    except Exception as error:
        logger.error(
            f"Got an error when initializing MongoDB database resource and Beanie: {error}"
        )
        raise

    logger.info("Running MongoDB Beanie migration...")
    try:
        os.system(
            f"beanie migrate -uri {mongodb_uri} -db {mongo_database_settings.database} "
            + "-p src/layers/data_access_layer/mongodb/migrations --forward --no-use-transaction"
        )
        logger.info("MongoDB Beanie migration run successfully.")
    except Exception as error:
        logger.error(f"Got an error when running MongoDB Beanie migration: {error}")
        raise

    logger.info("Closing MongoDB database resource...")
    if database.client:
        database.client.close()


if __name__ == "__main__":
    asyncio.run(main())
