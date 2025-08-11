import json
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from src.layers.business_layer.ai_agents.workflows.database_ingestion_workflow import (
    DatabaseIngestionWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.test_workflow_1 import TestWorkflow1
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
    test_workflow: DatabaseIngestionWorkflow = Depends(
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


@router.post(
    "/test-1",
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
@inject
async def test_1(
    response: Response,
    test_workflow_1: TestWorkflow1 = Depends(Provide[Container.test_workflow_1]),
):
    prompt = """
    Perform the following tasks in order:
    1. Generate only one random number.
    2. Check if the number is prime or not.
    3. Summarize the results of the activities above in a single answer.
    Each assistant can perform only one task and nothing beyond those described above..
    """
    input_message = prompt
    format_instructions_dict = {
        "title": "answer",
        "type": "object",
        "properties": {
            "number": {
                "type": "object",
                "description": "The number.",
                "properties": {
                    "value": {"type": "int", "description": "The number value."},
                    "is_prime": {
                        "type": "bool",
                        "description": "The boolean value that checks if the number is prime or not.",
                    },
                },
                "required": ["access_key", "issue_date", "total_value"],
            }
        },
        "required": ["number"],
    }
    schema_str = json.dumps(format_instructions_dict)
    format_instructions_str = f"""
    Your final answer MUST be a JSON object that strictly adheres to the following JSON schema. 
    Do not include any other text or explanations outside of the JSON object itself.\n
    ```json\n{schema_str}\n```
    """

    result = await test_workflow_1.run(
        input_message=input_message, format_instructions_str=format_instructions_str
    )
    answer: str = result["messages"][-1].content
    answer_as_json = json.loads(answer)
    logger.info(f"answer_as_json: {answer_as_json}")
    if answer_as_json["number"]["is_prime"] is True:
        logger.info("É primo!")
    else:
        logger.info("Não é primo!")
    logger.info(f"Final result: {answer}")
    return {}


@router.post(
    "/test-2",
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
@inject
async def test_2(
    response: Response,
    test_workflow_1: TestWorkflow1 = Depends(Provide[Container.test_workflow_1]),
):
    prompt = """
    Perform the following tasks in order:
    1. Generate only one random number.
    2. Check if the number is prime or not.
    3. Summarize the results of the activities above in a single answer.
    Each assistant can perform only one task and nothing beyond those described above..
    """
    input_message = prompt
    format_instructions_str = ""
    result = await test_workflow_1.run(
        input_message=input_message, format_instructions_str=format_instructions_str
    )
    answer: str = result["messages"][-1].content
    logger.info(f"answer: {answer}")
    return {}
