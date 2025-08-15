from typing import AsyncGenerator

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.business_layer.ai_agents.tools.insert_ingestion_args_into_database_tool import (
    InsertIngestionArgsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.general_data_analysis_workflow import (
    GeneralDataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.technical_data_analysis_workflow import (
    TechnicalDataAnalysisWorkflow,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    llm = providers.Singleton(LLM, ai_settings=config.ai_settings)

    postgresdb = providers.Singleton(
        PostgresDB, postgresdb_settings=config.postgresdb_settings
    )

    async def init_postgres_async_session(
        postgresdb: providers.Singleton,
    ) -> AsyncGenerator[AsyncSession, None]:
        async with postgresdb.async_session() as async_session:
            yield async_session

    postgresdb_async_session = providers.Resource(
        init_postgres_async_session,
        postgresdb=postgresdb,
    )

    unzip_files_from_zip_archive_tool = providers.Singleton(
        UnzipFilesFromZipArchiveTool
    )
    map_csvs_to_ingestion_args_tool = providers.Singleton(
        MapCSVsToIngestionArgsTool, ingestion_config_dict=config.ingestion_config_dict
    )
    insert_ingestion_args_into_database_tool = providers.Singleton(
        InsertIngestionArgsIntoDatabaseTool,
        postgresdb=postgresdb,
        sqlalchemy_model_by_table_name=config.sqlalchemy_model_by_table_name,
    )

    data_ingestion_workflow = providers.Singleton(
        DataIngestionWorkflow,
        chat_model=llm.provided.chat_model,
        unzip_files_from_zip_archive_tool=unzip_files_from_zip_archive_tool,
        map_csvs_to_ingestion_args_tool=map_csvs_to_ingestion_args_tool,
        insert_ingestion_args_into_database_tool=insert_ingestion_args_into_database_tool,
    )

    async_sql_database_toolkit = providers.Singleton(
        AsyncSQLDatabaseToolkit,
        postgresdb=postgresdb,
        chat_model=llm.provided.chat_model,
    )

    general_data_analysis_workflow = providers.Singleton(
        GeneralDataAnalysisWorkflow,
        chat_model=llm.provided.chat_model,
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
    )

    technical_data_analysis_workflow = providers.Singleton(
        TechnicalDataAnalysisWorkflow,
        chat_model=llm.provided.chat_model,
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
    )
