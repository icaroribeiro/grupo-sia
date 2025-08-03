from typing import AsyncGenerator

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
    InsertRecordsIntoDatabaseTool,
    MapCSVsToIngestionArgsTool,
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.general_data_analysis_workflow import (
    GeneralDataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.technical_data_analysis_workflow import (
    TechnicalDataAnalysisWorkflow,
)
from src.layers.core_logic_layer.chat_model.chat_model import ChatModel
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

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

    chat_model = providers.Singleton(ChatModel, ai_settings=config.ai_settings)

    unzip_files_from_zip_archive_tool = providers.Singleton(
        UnzipFilesFromZipArchiveTool
    )
    map_csvs_to_ingestion_args_tool = providers.Singleton(MapCSVsToIngestionArgsTool)
    # map_ingestion_args_to_db_models_tool = providers.Singleton(
    #     MapIngestionArgsToDBModelsTool
    # )
    insert_records_into_database_tool = providers.Singleton(
        InsertRecordsIntoDatabaseTool,
        postgresdb=postgresdb,
    )
    # insert_records_into_database_tool_2 = providers.Singleton(
    #     InsertRecordsIntoDatabaseTool2,
    #     postgresdb=postgresdb,
    # )
    # map_csvs_to_pydantic_models_tool = providers.Singleton(
    #     MapCSVsToPydanticModelsTool,
    # )
    # map_csvs_to_db_models_tool = providers.Singleton(MapCSVsToDBModelsTool)
    # insert_records_into_database_tool_3 = providers.Singleton(
    #     InsertRecordsIntoDatabaseTool3,
    #     postgresdb=postgresdb,
    # )
    # data_ingestion_agent = providers.Singleton(
    #     DataIngestionAgent,
    #     llm=chat_model.provided.llm,
    #     tools=providers.List(
    #         unzip_files_from_zip_archive_tool,
    #         map_csvs_to_ingestion_args_tool,
    #         map_ingestion_args_to_db_models_tool,
    #         # insert_records_into_database_tool,
    #     ),
    # )
    data_ingestion_workflow = providers.Singleton(
        DataIngestionWorkflow,
        llm=chat_model.provided.llm,
        unzip_files_from_zip_archive_tool=unzip_files_from_zip_archive_tool,
        map_csvs_to_ingestion_args_tool=map_csvs_to_ingestion_args_tool,
        # map_ingestion_args_to_db_models_tool=map_ingestion_args_to_db_models_tool,
        insert_records_into_database_tool=insert_records_into_database_tool,
        # map_csvs_to_db_models_tool=map_csvs_to_db_models_tool,
        # insert_records_into_database_tool_2=insert_records_into_database_tool_2,
        # map_csvs_to_pydantic_models_tool=map_csvs_to_pydantic_models_tool,
        # insert_records_into_database_tool_3=insert_records_into_database_tool_3,
    )

    async_sql_database_toolkit = providers.Singleton(
        AsyncSQLDatabaseToolkit,
        postgresdb=postgresdb,
        llm=chat_model.provided.llm,
    )

    general_data_analysis_workflow = providers.Singleton(
        GeneralDataAnalysisWorkflow,
        llm=chat_model.provided.llm,
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
    )

    technical_data_analysis_workflow = providers.Singleton(
        TechnicalDataAnalysisWorkflow,
        llm=chat_model.provided.llm,
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
    )
