from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from src.layers.core_logic_layer.logging import logger
from langchain_core.messages import AIMessage, ToolMessage  # noqa: F401

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )
from src.layers.core_logic_layer.container.container import Container
from src.layers.presentation_layer.rest_api.schemas.send_queries_schema import (
    SendQueryRequest,
    SendQueryResponse,
)
# from typing import AsyncGenerator

# from beanie import Document
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
# from src.layers.data_access_layer.mongodb.mongodb import MongoDB


router = APIRouter()


@router.post(
    "/send-query",
    response_model=SendQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def send_query(
    response: Response,
    send_query_request: SendQueryRequest,
    config: dict = Depends(Provide[Container.config]),
    postgresdb: PostgresDB = Depends(Provide[Container.postgresdb]),
):
    logger.info(f"send_query_request.query: {send_query_request.query}")

    # toolkit = AsyncSQLDatabaseToolkit(
    #     postgresdb=postgresdb, llm=data_analysis_worker_agent.llm
    # )
    # tools = toolkit.get_tools()

    # # Create LangGraph agent
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         (
    #             "system",
    #             "You are a SQL assistant. Use the provided tools to query the database and answer questions.",
    #         ),
    #         MessagesPlaceholder(variable_name="messages"),  # Use messages from state
    #     ]
    # )
    # agent = create_react_agent(data_analysis_worker_agent.llm, tools, prompt=prompt)

    # result = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": send_query_request.query}]}
    # )

    answer = ""
    # for message in result["messages"]:
    #     if isinstance(message, AIMessage):
    #         if message.content:
    #             print(f"Agent response: {message.content}")
    #             answer = message.content
    #         if message.tool_calls:
    #             print(f"Tool call: {message.tool_calls}")
    #     elif isinstance(message, ToolMessage):
    #         print(f"Tool response: {message.content} (Tool: {message.name})")

    return SendQueryResponse(answer=answer)
