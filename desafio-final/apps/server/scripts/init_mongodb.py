import asyncio
import os
from urllib.parse import quote


from src.layers.business_layer.ai_agents.tools.disconnect_from_mongodb_tool import (
    DisconnectFromMongoDBTool,
)
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.mongodb_settings import (
    MongoDBSettings,
)
from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.layers.business_layer.ai_agents.tools.connect_to_mongodb_tool import (
    ConnectToMongoDBTool,
)


async def main() -> None:
    logger.info("Started initiating MongoDB...")

    mongodb_settings = MongoDBSettings()
    mongodb_uri_template = "mongodb://{username}:{password}@{host}:{port}"
    mongodb_uri = mongodb_uri_template.format(
        username=quote(mongodb_settings.username),
        password=quote(mongodb_settings.password),
        host=mongodb_settings.host,
        port=mongodb_settings.port,
    )
    connect_to_mongodb_tool = ConnectToMongoDBTool()
    (message, result) = await connect_to_mongodb_tool._arun(
        uri=mongodb_uri,
        database_name=mongodb_settings.database,
        documents=[InvoiceDocument, InvoiceItemDocument],
    )
    database: AsyncIOMotorDatabase | None = None
    if result is None:
        raise Exception(message)
    database = result

    logger.info("Started running MongoDB Beanie migration...")
    try:
        os.system(
            f"beanie migrate -uri {mongodb_uri} -db {mongodb_settings.database} "
            + "-p mongodb/migrations --forward --no-use-transaction"
        )
        message = "Success: MongoDB Beanie migration complete."
        logger.info(message)
    except Exception as error:
        message = f"Error: Failed to run MongoDB Beanie migration: {error}"
        logger.error(message)
        raise Exception(message)

    disconnect_from_mongodb_tool = DisconnectFromMongoDBTool()
    (message, result) = disconnect_from_mongodb_tool._run(database=database)
    if "Error" in message:
        raise Exception(message)


if __name__ == "__main__":
    asyncio.run(main())
