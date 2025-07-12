import asyncio
import os
from typing import Union
from urllib.parse import quote
from beanie import Document
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.layers.business_layer.ai_agents.tools.connect_to_mongodb_tool import (
    ConnectToMongoDBTool,
)
from src.layers.business_layer.ai_agents.tools.disconnect_from_mongodb_tool import (
    DisconnectFromMongoDBTool,
)
from src.layers.business_layer.ai_agents.tools.insert_to_mongodb_tool import (
    InsertToMongoDBTool,
)
from src.layers.business_layer.ai_agents.tools.list_documents_from_csv_tool import (
    ListDocumentsFromCSVTool,
)
from src.layers.business_layer.ai_agents.tools.map_csv_to_ingestion_args_tool import (
    MapCSVToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_file_tool import UnzipFileTool
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import mongodb_settings
from src.layers.core_logic_layer.settings import app_settings
from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)


async def main() -> None:
    logger.info("Started importing CSV files to MongoDB...")

    data_dir_path = app_settings.imports_data_dir_path
    extracted_data_dir_path = os.path.join(data_dir_path, "extracted")
    unzip_file_tool = UnzipFileTool()
    (message, result) = unzip_file_tool._run(
        dir_path=data_dir_path, destionation_dir_path=extracted_data_dir_path
    )
    extracted_file_paths: list[str] = list()
    if result is None:
        raise Exception(message)
    extracted_file_paths = result

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

    documents_map: dict[str, list[Document]] = dict()
    map_csv_to_ingestion_args_tool = MapCSVToIngestionArgsTool()
    (message, result) = map_csv_to_ingestion_args_tool._run(
        file_paths=extracted_file_paths
    )
    if result is None:
        raise Exception(message)
    ingestion_args_map = result

    for injestion_args_list in ingestion_args_map.values():
        for ingestion_args in injestion_args_list:
            file_path = ingestion_args.file_path
            document_class: Union[InvoiceDocument, InvoiceItemDocument] = (
                ingestion_args.document_class
            )
            list_documents_from_csv_tool = ListDocumentsFromCSVTool()
            (message, result) = list_documents_from_csv_tool._run(
                file_path=file_path,
                document_class=document_class,
            )
            if result is None:
                raise Exception(message)
            document_class_name = ingestion_args.document_class.Settings.name
            if documents_map.get(document_class_name, None) is None:
                documents_map[document_class_name] = result
            else:
                documents_map[document_class_name] += result

    insert_to_mongodb_tool = InsertToMongoDBTool()
    (message, result) = await insert_to_mongodb_tool._arun(documents_map=documents_map)
    if result is None:
        raise Exception(message)

    disconnect_from_mongodb_tool = DisconnectFromMongoDBTool()
    (message, result) = disconnect_from_mongodb_tool._run(database=database)
    if "Error" in message:
        raise Exception(message)


if __name__ == "__main__":
    asyncio.run(main())
