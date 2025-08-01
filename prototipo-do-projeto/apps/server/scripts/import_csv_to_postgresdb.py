import asyncio
import os
from typing import Tuple

from src.layers.business_layer.ai_agents.models.invoice_ingestion_args import (
    InvoiceIngestionArgs,
)
from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_args import (
    InvoiceItemIngestionArgs,
)
from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.business_layer.ai_agents.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.map_ingestion_args_to_db_models_tool import (
    MapIngestionArgsToDBModelsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import app_settings
from src.layers.core_logic_layer.settings.postgresdb_settings import PostgresDBSettings
from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import InvoiceModel
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


async def main() -> None:
    logger.info("Importing CSV files to PostgresDB has started...")

    dir_path = app_settings.imports_data_dir_path
    file_path = os.path.join(dir_path, "200001_NFe.zip")
    extracted_data_dir_path = os.path.join(dir_path, "extracted")
    unzip_files_from_zip_archive_tool = UnzipFilesFromZipArchiveTool()
    tool_output: ToolOutput = unzip_files_from_zip_archive_tool._run(
        file_path=file_path, destionation_dir_path=extracted_data_dir_path
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return
    extracted_file_paths: list[str] = tool_output.result

    map_csvs_to_ingestion_args_tool = MapCSVsToIngestionArgsTool()
    tool_output: ToolOutput = map_csvs_to_ingestion_args_tool._run(
        file_paths=extracted_file_paths
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return
    ingestion_args_dict: dict[
        Tuple[int, str], list[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
    ] = tool_output.result

    map_ingestion_args_to_db_models_tool = MapIngestionArgsToDBModelsTool()
    tool_output: ToolOutput = map_ingestion_args_to_db_models_tool._run(
        ingestion_args_dict=ingestion_args_dict
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return
    models_dict: dict[Tuple[int, str], list[InvoiceModel | InvoiceItemModel]] = (
        tool_output.result
    )

    postgresdb_settings = PostgresDBSettings()
    postgresdb = PostgresDB(postgresdb_settings=postgresdb_settings)
    insert_models_into_postgresdb_tool = InsertRecordsIntoDatabaseTool(
        postgresdb=postgresdb
    )
    tool_output: ToolOutput = await insert_models_into_postgresdb_tool._arun(
        models_dict=models_dict
    )
    if tool_output.result is None:
        logger.error(tool_output.message)
        return


if __name__ == "__main__":
    asyncio.run(main())
