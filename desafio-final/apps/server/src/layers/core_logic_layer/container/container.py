from typing import AsyncGenerator

from beanie import Document
from dependency_injector import containers, providers
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.layers.business_layer.ai_agents.agents.manager_agent_1 import ManagerAgent_1
from src.layers.business_layer.ai_agents.agents.assistant_agents import (
    AssistentAgent_1,
    AssistentAgent_2,
    AssistentAgent_3,
)
from src.layers.business_layer.ai_agents.agents.supervisor_agent_1 import (
    SupervisorAgent_1,
)
from src.layers.business_layer.ai_agents.graphs.subgraph_1 import Subgraph_1
from src.layers.business_layer.ai_agents.graphs.subgraph_2 import Subgraph_2
from src.layers.business_layer.ai_agents.graphs.parent_graph_1 import ParentGraph_1
from src.layers.core_logic_layer.llm.llm import LLM
from src.layers.data_access_layer.mongodb.mongodb import MongoDB


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    mongodb = providers.Singleton(MongoDB, mongodb_settings=config.mongodb_settings)

    async def init_mongodb_client(
        mongodb: providers.Singleton,
    ) -> AsyncGenerator[AsyncIOMotorClient, None]:
        async for client in mongodb.client:
            yield client

    mongodb_client_resource = providers.Resource(
        init_mongodb_client,
        mongodb=mongodb,
    )

    async def init_mongodb_database(
        mongodb: providers.Singleton, config: providers.Configuration
    ) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
        database_name: str = config["mongodb_settings"].database
        documents: list[Document] = config["mongodb_beanie_documents"]
        async for database in mongodb.init_database(
            database_name=database_name, documents=documents
        ):
            yield database

    mongodb_database_resource = providers.Resource(
        init_mongodb_database,
        mongodb=mongodb,
        config=config,
    )

    llm = providers.Singleton(LLM, ai_settings=config.ai_settings)

    # assistant_agent_1 = providers.Singleton(
    #     Agent,
    #     name="assistant_agent_1",
    #     prompt="""
    #     You are a helpful assistant tasked with creating random numbers.
    #     """,
    #     llm=llm_resource,
    #     tools=[CreateRandomNumberTool()],
    # )

    assistant_agent_1 = providers.Singleton(AssistentAgent_1, llm=llm.provided.llm)

    subgraph_1 = providers.Singleton(
        Subgraph_1, name="Subgraph_1", assistant_agent_1=assistant_agent_1
    )

    assistant_agent_2 = providers.Singleton(AssistentAgent_2, llm=llm.provided.llm)

    assistant_agent_3 = providers.Singleton(AssistentAgent_3, llm=llm.provided.llm)

    supervisor_agent_1 = providers.Singleton(
        SupervisorAgent_1,
        llm=llm.provided.llm,
    )

    subgraph_2 = providers.Singleton(
        Subgraph_2,
        name="Subgraph_2",
        assistant_agent_2=assistant_agent_2,
        assistant_agent_3=assistant_agent_3,
        supervisor_agent_1=supervisor_agent_1,
    )

    manager_agent_1 = providers.Singleton(
        ManagerAgent_1,
        llm=llm.provided.llm,
    )

    parent_graph_1 = providers.Singleton(
        ParentGraph_1,
        name="ParentGraph_1",
        subgraph_2=subgraph_2,
        manager_agent_1=manager_agent_1,
    )

    # parent_graph = providers.Singleton(
    #     ParentGraph,
    #     name="ParentGraph",
    #     subgraph_1=subgraph_1,
    #     supervisor_agent_1=supervisor_agent_1,
    # )

    # test_workflow = providers.Singleton(
    #     TestWorkflow,
    #     name="TestWorkflow",
    #     assistant_agent_1=assistant_agent_1,
    #     agent2=agent2,
    #     agent3=agent3,
    #     supervisor_agent_1=supervisor_agent_1,
    # )

    # data_ingestion_agent = providers.Singleton(DataIngestionAgent, llm=llm_resource)

    # def init_data_ingestion_agent(
    #     data_ingestion_agent: providers.Singleton,
    # ) -> Runnable[BaseMessage, BaseMessage]:
    #     return data_ingestion_agent.agent

    # data_ingestion_agent_resource = providers.Resource(
    #     init_data_ingestion_agent,
    #     data_ingestion_agent=data_ingestion_agent,
    # )

    # data_ingestion_workflow = providers.Singleton(
    #     DataIngestionWorkflow,
    #     data_ingestion_agent=data_ingestion_agent_resource,
    # )

    # llm_resource = providers.Resource(llm, config=config)

    # data_ingestion_crew = providers.Singleton(DataIngestionCrew, llm=llm_resource)

    # crew_orchestrator = providers.Singleton(
    #     CrewOrchestrator, config=config, data_ingestion_crew=data_ingestion_crew
    # )

    # async def mongodb_client(
    #     config: providers.Configuration,
    # ) -> AsyncGenerator[AsyncIOMotorClient]:
    #     logger.info("Initiating MongoDB client resource...")
    #     client = AsyncIOMotorClient(
    #         config["mongodb_params"]["uri"],
    #     )
    #     try:
    #         await client["admin"].command("ping")
    #         message = "Success: MongoDB client resource initiated."
    #         logger.info(message)
    #         yield client
    #     except Exception as error:
    #         message = f"Error: Failed to initiate MongoDB client resource: {error}"
    #         logger.error(message)
    #         raise Exception(message)
    #     finally:
    #         logger.info("Closing MongoDB client resource...")
    #         if client:
    #             client.close()

    # async def mongodb_database(
    #     client: AsyncIOMotorClient,
    #     config: providers.Configuration,
    # ) -> AsyncGenerator[AsyncIOMotorDatabase]:
    #     logger.info("Initiating MongoDB database resource and Beanie...")
    #     database = client[config["mongodb_params"]["database_name"]]
    #     try:
    #         await init_beanie(
    #             database=database,
    #             document_models=[
    #                 InvoiceDocument,
    #                 InvoiceItemDocument,
    #             ],
    #         )
    #         message = "Success: MongoDB database resource and Beanie initialized."
    #         logger.info(message)
    #         yield database
    #     except Exception as error:
    #         message = "Error: Failed to initiate MongoDB database resource "
    #         f"and Beanie: {error}"
    #         logger.error(message)
    #         raise Exception(message)
    #     finally:
    #         logger.info("Closing MongoDB database resource...")
    #         if database.client:
    #             database.client.close()

    # mongodb_client_resource = providers.Resource(mongodb_client, config=config)

    # mongodb_database_resource = providers.Resource(
    #     mongodb_database, client=mongodb_client_resource, config=config
    # )

    # mongodb_resource = providers.Resource(mongodb, config=config)

    # async def llm(config: providers.Configuration) -> LLM:
    #     logger.info("Initiating LLM...")
    #     llm_name = config["llm"]
    #     openai_api_key = config["openai_api_key"]
    #     gemini_api_key = config["gemini_api_key"]
    #     temperature = config["temperature"]

    #     if llm_name.lower() not in ["gpt", "gemini"]:
    #         message = (
    #             "LLM not configured. "
    #             + "You must set up a LLM in your .env file or environment variables."
    #         )
    #         logger.error(message)
    #         raise Exception(message)

    #     llm: LLM
    #     if llm_name.lower() == "gpt":
    #         if not openai_api_key:
    #             message = (
    #                 "OPENAI_API_KEY not configured. "
    #                 + "You must set up an API key in your .env file or environment variables."
    #             )
    #             logger.error(message)
    #             raise Exception(message)
    #         else:
    #             llm = GPTMiniLLM.create(
    #                 temperature=temperature, api_key=openai_api_key
    #             ).llm

    #     if llm_name.lower() == "gemini":
    #         if not gemini_api_key:
    #             message = (
    #                 "GEMINI_API_KEY not configured. "
    #                 + "You must set up an API key in your .env file or environment variables."
    #             )
    #             logger.error(message)
    #             raise Exception(message)
    #         else:
    #             llm = GeminiFlashLLM.create(
    #                 temperature=temperature, api_key=gemini_api_key
    #             ).llm

    #     logger.info("LLM initialized successfully.")
    #     return llm

    # llm_resource = providers.Resource(llm, config=config)

    # data_ingestion_crew = providers.Singleton(DataIngestionCrew, llm=llm_resource)

    # crew_orchestrator = providers.Singleton(
    #     CrewOrchestrator, config=config, data_ingestion_crew=data_ingestion_crew
    # )
