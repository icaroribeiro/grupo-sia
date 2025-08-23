import asyncio
import os


from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_config_model import (
    InvoiceItemIngestionConfig,
)
from src.layers.business_layer.ai_agents.models.invoice_ingestion_config_model import (
    InvoiceIngestionConfig,
)
from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.business_layer.ai_agents.tools.insert_ingestion_args_into_database_tool import (
    InsertIngestionArgsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.core_logic_layer.logging import logger

from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.core_logic_layer.settings import app_settings
from src.layers.core_logic_layer.settings.postgresdb_settings import PostgresDBSettings
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB
from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel as SQLAlchemyInvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import (
    InvoiceModel as SQLAlchemyInvoiceModel,
)


async def main() -> None:
    logger.info("Importing CSV files to PostgresDB has started...")

    dir_path = app_settings.uploads_data_dir_path
    file_path = os.path.join(dir_path, "200001_NFe.zip")
    extracted_data_dir_path = os.path.join(dir_path, "extracted")
    unzip_files_from_zip_archive_tool = UnzipFilesFromZipArchiveTool()
    tool_output: ToolOutput = await unzip_files_from_zip_archive_tool._arun(
        file_path=file_path, destination_dir_path=extracted_data_dir_path
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return
    logger.info(f"tool_output: {tool_output}")
    extracted_file_paths: list[str] = tool_output.result

    dir_path = app_settings.imports_data_dir_path
    invoice_ingestion_args_dict = InvoiceIngestionConfig().model_dump()
    invoice_item_ingestion_args_dict = InvoiceItemIngestionConfig().model_dump()
    ingestion_config_dict = {
        0: invoice_ingestion_args_dict,
        1: invoice_item_ingestion_args_dict,
    }
    map_csvs_to_ingestion_args_tool = MapCSVsToIngestionArgsTool(
        ingestion_config_dict=ingestion_config_dict
    )
    tool_output: ToolOutput = await map_csvs_to_ingestion_args_tool._arun(
        file_paths=extracted_file_paths, destination_dir_path=dir_path
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return
    logger.info(f"tool_output: {tool_output}")
    ingestion_args_list: list[dict[str, str]] = tool_output.result

    postgresdb_settings = PostgresDBSettings()
    postgresdb = PostgresDB(postgresdb_settings=postgresdb_settings)
    sqlalchemy_model_by_table_name = {
        SQLAlchemyInvoiceModel.get_table_name(): SQLAlchemyInvoiceModel,
        SQLAlchemyInvoiceItemModel.get_table_name(): SQLAlchemyInvoiceItemModel,
    }
    insert_ingestion_args_into_database_tool = InsertIngestionArgsIntoDatabaseTool(
        postgresdb=postgresdb,
        sqlalchemy_model_by_table_name=sqlalchemy_model_by_table_name,
        ingestion_config_dict=ingestion_config_dict,
    )
    tool_output: ToolOutput = await insert_ingestion_args_into_database_tool._arun(
        ingestion_args_list=ingestion_args_list
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return
    logger.info(f"tool_output: {tool_output}")


if __name__ == "__main__":
    asyncio.run(main())
