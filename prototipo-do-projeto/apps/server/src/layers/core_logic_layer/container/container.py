# from typing import AsyncGenerator

# from beanie import Document
from typing import AsyncGenerator
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession
from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.agents.data_ingestion_agent import (
    DataIngestionAgent,
)
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.business_layer.ai_agents.tools.map_files_to_ingestion_args_tool import (
    MapFilesToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.list_files_from_zip_archive_tool import (
    ListFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.tools.map_ingestion_args_to_models_tool import (
    MapIngestionArgsToModelsTool,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB

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
from src.layers.core_logic_layer.chat_model.chat_model import ChatModel
# from src.layers.data_access_layer.mongodb.mongodb import MongoDB


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # mongodb = providers.Singleton(MongoDB, mongodb_settings=config.mongodb_settings)

    # async def init_mongodb_client(
    #     mongodb: providers.Singleton,
    # ) -> AsyncGenerator[AsyncIOMotorClient, None]:
    #     async for client in mongodb.client:
    #         yield client

    # mongodb_client_resource = providers.Resource(
    #     init_mongodb_client,
    #     mongodb=mongodb,
    # )

    # async def init_mongodb_database(
    #     mongodb: providers.Singleton, config: providers.Configuration
    # ) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    #     database_name: str = config["mongodb_settings"].database
    #     documents: list[Document] = config["mongodb_beanie_documents"]
    #     async for database in mongodb.init_database(
    #         database_name=database_name, documents=documents
    #     ):
    #         yield database

    # mongodb_database_resource = providers.Resource(
    #     init_mongodb_database,
    #     mongodb=mongodb,
    #     config=config,
    # )

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

    list_files_from_zip_archive_tool = providers.Singleton(ListFilesFromZipArchiveTool)
    map_files_to_ingestion_args_list = providers.Singleton(MapFilesToIngestionArgsTool)
    list_models_from_file = providers.Singleton(MapIngestionArgsToModelsTool)
    data_ingestion_agent = providers.Singleton(
        DataIngestionAgent,
        llm=chat_model.provided.llm,
        tools=[
            list_files_from_zip_archive_tool(),
            map_files_to_ingestion_args_list(),
            list_models_from_file(),
        ],
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
