import json

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from langchain_core.messages import AIMessage, ToolMessage  # noqa: F401

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )
from src.layers.business_layer.ai_agents.workflows.general_data_analysis_workflow import (
    GeneralDataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.technical_data_analysis_workflow import (
    TechnicalDataAnalysisWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.send_queries_schema import (
    SendGeneralQueryRequest,
    SendGeneralQueryResponse,
    SendTechnicalQueryRequest,
    SendTechnicalQueryResponse,
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
    response_model=SendGeneralQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@inject
async def send_general_queries(
    response: Response,
    send_general_query_request: SendGeneralQueryRequest,
    general_data_analysis_workflow: GeneralDataAnalysisWorkflow = Depends(
        Provide[Container.general_data_analysis_workflow]
    ),
):
    prompt = """
    Respond to the following request or question objectively:
    {query}
    """
    input_message = prompt.format(query=send_general_query_request.query)

    result = await general_data_analysis_workflow.run(input_message=input_message)
    answer: str = result["messages"][-1].content
    logger.info(f"Final result: {answer}")
    return SendGeneralQueryResponse(answer=answer)


@router.post(
    "/send-technical-queries",
    response_model=SendTechnicalQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@inject
async def send_technical_queries(
    response: Response,
    send_technical_query_request: SendTechnicalQueryRequest,
    technical_data_analysis_workflow: TechnicalDataAnalysisWorkflow = Depends(
        Provide[Container.technical_data_analysis_workflow]
    ),
):
    prompt = """
    Respond to the following request or question objectively:
    {query}
    """
    input_message = prompt.format(query=send_technical_query_request.query)

    format_instructions_str = ""
    # If a dictionary is provided, create the instruction string.
    if send_technical_query_request.format_instructions_dict:
        # This creates a string similar to what JsonOutputParser().get_format_instructions() would produce.
        schema_str = json.dumps(
            send_technical_query_request.format_instructions_dict, indent=2
        )
        format_instructions_str = f"""
        Your final answer MUST be a JSON object that strictly adheres to the following JSON schema. 
        Do not include any other text or explanations outside of the JSON object itself.\n
        ```json\n{schema_str}\n```
        """
    # logger.info(f"format_instructions_str: {format_instructions_str}")

    result = await technical_data_analysis_workflow.run(
        input_message=input_message, format_instructions_str=format_instructions_str
    )
    answer: str = result["messages"][-1].content
    logger.info(f"Final result: {answer}")
    return SendTechnicalQueryResponse(answer=json.loads(s=answer))
