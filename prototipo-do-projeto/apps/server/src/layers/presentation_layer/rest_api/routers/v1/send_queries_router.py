from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from langchain_core.messages import AIMessage, ToolMessage  # noqa: F401

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )
from langchain_core.prompts import ChatPromptTemplate

from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.send_queries_schema import (
    SendQueryRequest,
    SendQueryResponse,
)

# from typing import AsyncGenerator

# from beanie import Document
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
    "/send-general-queries",
    response_model=SendQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def send_general_queries(
    response: Response,
    send_query_request: SendQueryRequest,
    data_analysis_agent: DataAnalysisAgent = Depends(
        Provide[Container.data_analysis_agent]
    ),
):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "human",
                """
                Respond to the following question objectively:
                {query}
                """,
            ),
        ]
    )
    formatted_content = prompt.format(query=send_query_request.query)
    agent = data_analysis_agent.agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": formatted_content}]}
    )
    content: str = result["messages"][-1].content
    logger.info(f"content: {content}")
    return SendQueryResponse(answer=content)


@router.post(
    "/send-technical-queries",
    response_model=SendQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def send_technical_queries(
    response: Response,
    send_query_request: SendQueryRequest,
    data_analysis_agent: DataAnalysisAgent = Depends(
        Provide[Container.data_analysis_agent]
    ),
):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "human",
                """
                Respond to the following question with only a valid SQL statement, 
                without any additional explanation or information:
                {query}
                """,
            ),
        ]
    )
    formatted_content = prompt.format(query=send_query_request.query)
    agent = data_analysis_agent.agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": formatted_content}]}
    )
    content: str = result["messages"][-1].content
    logger.info(f"content: {content}")
    return SendQueryResponse(answer=content)
