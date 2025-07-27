import asyncio
import os


from src.layers.business_layer.ai_agents.tools.insert_records_to_postgresdb_tool import (
    InsertRecordsToPostgresDBTool,
)
from src.layers.business_layer.ai_agents.tools.map_ingestion_args_to_models_tool import (
    MapIngestionArgsToModelDictTool,
)
from src.layers.business_layer.ai_agents.tools.map_files_to_ingestion_args_tool import (
    MapFilesToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_file_tool import UnzipFileTool
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import app_settings


async def main() -> None:
    logger.info("Started importing CSV files to PostgresDB...")

    dir_path = app_settings.imports_data_dir_path
    file_path = os.path.join(dir_path, "200001_NFe.zip")
    extracted_data_dir_path = os.path.join(dir_path, "extracted")
    unzip_file_tool = UnzipFileTool()
    (message, result) = unzip_file_tool._run(
        file_path=file_path, destionation_dir_path=extracted_data_dir_path
    )
    extracted_file_paths: list[str] = list()
    if result is None:
        raise Exception(message)
    extracted_file_paths = result

    # mongodb_uri_template = "mongodb://{username}:{password}@{host}:{port}"
    # mongodb_uri = mongodb_uri_template.format(
    #     username=quote(mongodb_settings.username),
    #     password=quote(mongodb_settings.password),
    #     host=mongodb_settings.host,
    #     port=mongodb_settings.port,
    # )
    # connect_to_mongodb_tool = ConnectToMongoDBTool()
    # (message, result) = await connect_to_mongodb_tool._arun(
    #     uri=mongodb_uri,
    #     database_name=mongodb_settings.database,
    #     documents=[InvoiceDocument, InvoiceItemDocument],
    # )
    # database: AsyncIOMotorDatabase | None = None
    # if result is None:
    #     raise Exception(message)
    # database = result

    map_files_to_ingestion_args_tool = MapFilesToIngestionArgsTool()
    (message, result) = map_files_to_ingestion_args_tool._run(
        file_paths=extracted_file_paths
    )
    if result is None:
        raise Exception(message)
    ingestion_args_list = result

    map_ingestion_args_to_models_tool = MapIngestionArgsToModelDictTool()
    (message, result) = map_ingestion_args_to_models_tool._run(
        ingestion_args_list=ingestion_args_list
    )
    if result is None:
        raise Exception(message)
    print(f"result: {result}")
    # document_class_name = ingestion_args.document_class.Settings.name
    # if documents_map.get(document_class_name, None) is None:
    #     documents_map[document_class_name] = result
    # else:
    #     documents_map[document_class_name] += result

    insert_records_to_postgresdb_tool = InsertRecordsToPostgresDBTool()
    (message, result) = await insert_records_to_postgresdb_tool._arun(
        model_classes=result
    )
    if result is None:
        raise Exception(message)

    # disconnect_from_mongodb_tool = DisconnectFromMongoDBTool()
    # (message, result) = disconnect_from_mongodb_tool._run(database=database)
    # if "Error" in message:
    #     raise Exception(message)


if __name__ == "__main__":
    asyncio.run(main())
