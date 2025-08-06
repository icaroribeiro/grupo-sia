import json
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from src.layers.business_layer.ai_agents.workflows.database_data_ingestion_workflow import (
    DatabaseDataIngestionWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger

router = APIRouter()


@router.post(
    "/test",
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
@inject
async def test(
    response: Response,
    test_workflow: DatabaseDataIngestionWorkflow = Depends(
        Provide[Container.test_workflow]
    ),
):
    prompt = """
    Perform the following tasks in order:
    1. Generate only one random number.
    2. Respond the number and tell me if it's prime or not.
    Each assistant can perform only one task and nothing beyond those described above..
    """
    input_message = prompt

    result = await test_workflow.run(input_message=input_message)
    answer: str = result["messages"][-1].content
    answer_as_json = json.loads(answer)
    logger.info(answer_as_json)
    if answer_as_json["tool_output"]["result"] is True:
        logger.info("É primo!")
    else:
        logger.info("Não é primo!")
    logger.info(f"Final result: {answer}")
    return {}
