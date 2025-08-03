# from typing import AsyncGenerator

# from beanie import Document
from typing import AsyncGenerator

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)

# from src.layers.business_layer.ai_agents.tools.insert_records_into_database_tool import (
#     InsertRecordsIntoDatabaseTool,
# )
# from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
#     MapCSVsToIngestionArgsTool,
# )
# from src.layers.business_layer.ai_agents.tools.map_ingestion_args_to_db_models_tool import (
#     MapIngestionArgsToDBModelsTool,
# )
# from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
#     UnzipFilesFromZipArchiveTool,
# )
# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
# from src.layers.business_layer.ai_agents.agents.worker_agents import (
#     WorkerAgent_1,
#     WorkerAgent_2,
#     WorkerAgent_3,
# )
# from src.layers.business_layer.ai_agents.agents.parent_agent_1 import ParentAgent_1
# from src.layers.business_layer.ai_agents.agents.sub_agent_1 import (
#     SubAgent_1,
# )
# from src.layers.business_layer.ai_agents.graphs.subgraph_1 import Subgraph_1
# from src.layers.business_layer.ai_agents.graphs.subgraph_2 import Subgraph_2
# from src.layers.business_layer.ai_agents.graphs.parent_graph_1 import ParentGraph_1
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
    InsertRecordsIntoDatabaseTool,
    MapCSVsToIngestionArgsTool,
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.general_data_analysis_workflow import (
    GeneralDataAnalysisWorkflow,
)
from src.layers.core_logic_layer.chat_model.chat_model import ChatModel
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB

# from src.layers.data_access_layer.mongodb.mongodb import MongoDB


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
    data_analysis_agent = providers.Singleton(
        DataAnalysisAgent,
        llm=chat_model.provided.llm,
        tools=async_sql_database_toolkit.provided.get_tools.call(),
    )

    general_data_analysis_workflow = providers.Singleton(
        GeneralDataAnalysisWorkflow,
        llm=chat_model.provided.llm,
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
    )

    # worker_agent_1 = providers.Singleton(WorkerAgent_1, llm=llm.provided.llm)

    # subgraph_1 = providers.Singleton(
    #     Subgraph_1, name="Subgraph_1", worker_agent_1=worker_agent_1
    # )

    # worker_agent_2 = providers.Singleton(WorkerAgent_2, llm=llm.provided.llm)

    # worker_agent_3 = providers.Singleton(WorkerAgent_3, llm=llm.provided.llm)

    # sub_agent_1 = providers.Singleton(
    #     SubAgent_1,
    #     llm=llm.provided.llm,
    # )

    # subgraph_2 = providers.Singleton(
    #     Subgraph_2,
    #     name="Subgraph_2",
    #     worker_agent_2=worker_agent_2,
    #     worker_agent_3=worker_agent_3,
    #     sub_agent_1=sub_agent_1,
    # )

    # parent_agent_1 = providers.Singleton(
    #     ParentAgent_1,
    #     llm=llm.provided.llm,
    # )

    # parent_graph_1 = providers.Singleton(
    #     ParentGraph_1,
    #     name="ParentGraph_1",
    #     subgraph_2=subgraph_2,
    #     parent_agent_1=parent_agent_1,
    # )
