from typing import Annotated, Any

from fastapi import Depends
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.models.invoice_ingestion_config_model import (
    InvoiceIngestionConfigModel,
)
from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_config_model import (
    InvoiceItemIngestionConfigModel,
)
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.business_layer.ai_agents.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.layers.core_logic_layer.settings.app_settings import AppSettings
from src.layers.core_logic_layer.settings.postgresdb_settings import PostgresDBSettings

from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel as SQLAlchemyInvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import (
    InvoiceModel as SQLAlchemyInvoiceModel,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class Dependencies:
    @staticmethod
    def get_ai_settings() -> AISettings:
        return AISettings()

    @staticmethod
    def get_app_settings() -> AppSettings:
        return AppSettings()

    @staticmethod
    def get_postgresdb_settings() -> PostgresDBSettings:
        return PostgresDBSettings()

    @staticmethod
    def get_ingestion_config_dict() -> dict[int, dict[str, Any]]:
        return {
            0: InvoiceIngestionConfigModel().model_dump(),
            1: InvoiceItemIngestionConfigModel().model_dump(),
        }

    @staticmethod
    def get_sqlalchemy_model_by_table_name() -> dict[
        str, SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel
    ]:
        return {
            SQLAlchemyInvoiceModel.get_table_name(): SQLAlchemyInvoiceModel,
            SQLAlchemyInvoiceItemModel.get_table_name(): SQLAlchemyInvoiceItemModel,
        }

    @staticmethod
    def get_llm(ai_settings: Annotated[AISettings, Depends(get_ai_settings)]) -> LLM:
        return LLM(ai_settings=ai_settings)

    @staticmethod
    def get_postgresdb(
        postgresdb_settings: Annotated[
            PostgresDBSettings, Depends(get_postgresdb_settings)
        ],
    ) -> PostgresDB:
        return PostgresDB(postgresdb_settings=postgresdb_settings)

    @staticmethod
    def get_unzip_files_from_zip_archive_tool() -> UnzipFilesFromZipArchiveTool:
        return UnzipFilesFromZipArchiveTool()

    @staticmethod
    def get_map_csvs_to_ingestion_args_tool(
        ingestion_config_dict: Annotated[
            dict[int, dict[str, Any]], Depends(get_ingestion_config_dict)
        ],
    ) -> MapCSVsToIngestionArgsTool:
        return MapCSVsToIngestionArgsTool(ingestion_config_dict=ingestion_config_dict)

    @staticmethod
    def get_insert_records_into_database_tool(
        postgresdb: Annotated[PostgresDB, Depends(get_postgresdb)],
        ingestion_config_dict: Annotated[
            dict[int, dict[str, Any]], Depends(get_ingestion_config_dict)
        ],
        sqlalchemy_model_by_table_name: Annotated[
            dict[str, SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel],
            Depends(get_sqlalchemy_model_by_table_name),
        ],
    ) -> InsertRecordsIntoDatabaseTool:
        return InsertRecordsIntoDatabaseTool(
            postgresdb=postgresdb,
            ingestion_config_dict=ingestion_config_dict,
            sqlalchemy_model_by_table_name=sqlalchemy_model_by_table_name,
        )

    @staticmethod
    def get_async_sql_database_toolkit(
        postgresdb: Annotated[PostgresDB, Depends(get_postgresdb)],
        llm: Annotated[LLM, Depends(get_llm)],
    ) -> AsyncSQLDatabaseToolkit:
        return AsyncSQLDatabaseToolkit(
            postgresdb=postgresdb,
            chat_model=llm.chat_model,
        )

    @staticmethod
    def get_data_ingestion_workflow(
        app_settings: Annotated[AppSettings, Depends(get_app_settings)],
        llm: Annotated[LLM, Depends(get_llm)],
        unzip_files_from_zip_archive_tool: Annotated[
            UnzipFilesFromZipArchiveTool, Depends(get_unzip_files_from_zip_archive_tool)
        ],
        map_csvs_to_ingestion_args_tool: Annotated[
            MapCSVsToIngestionArgsTool, Depends(get_map_csvs_to_ingestion_args_tool)
        ],
        insert_records_into_database_tool: Annotated[
            InsertRecordsIntoDatabaseTool,
            Depends(get_insert_records_into_database_tool),
        ],
    ) -> DataIngestionWorkflow:
        return DataIngestionWorkflow(
            app_settings=app_settings,
            chat_model=llm.chat_model,
            unzip_files_from_zip_archive_tool=unzip_files_from_zip_archive_tool,
            map_csvs_to_ingestion_args_tool=map_csvs_to_ingestion_args_tool,
            insert_records_into_database_tool=insert_records_into_database_tool,
        )

    @staticmethod
    def get_data_analysis_workflow(
        app_settings: Annotated[AppSettings, Depends(get_app_settings)],
        llm: Annotated[LLM, Depends(get_llm)],
        async_sql_database_toolkit: Annotated[
            AsyncSQLDatabaseToolkit, Depends(get_async_sql_database_toolkit)
        ],
    ) -> DataAnalysisWorkflow:
        return DataAnalysisWorkflow(
            app_settings=app_settings,
            chat_model=llm.chat_model,
            async_query_sql_database_tools=async_sql_database_toolkit.get_tools(),
        )

    @staticmethod
    def get_top_level_workflow(
        app_settings: Annotated[AppSettings, Depends(get_app_settings)],
        llm: Annotated[LLM, Depends(get_llm)],
        data_ingestion_workflow: Annotated[
            DataIngestionWorkflow, Depends(get_data_ingestion_workflow)
        ],
        data_analysis_workflow: Annotated[
            DataAnalysisWorkflow, Depends(get_data_analysis_workflow)
        ],
    ) -> TopLevelWorkflow:
        return TopLevelWorkflow(
            app_settings=app_settings,
            chat_model=llm.chat_model,
            data_ingestion_workflow=data_ingestion_workflow,
            data_analysis_workflow=data_analysis_workflow,
        )
