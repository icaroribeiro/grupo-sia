import json

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.data_reporting_schema import (
    DataReportingRequest,
    DataReportingResponse,
)

router = APIRouter()


@router.post(
    "/data-reporting",
    response_model=DataReportingResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@inject
async def data_reporting(
    response: Response,
    data_reporting_request: DataReportingRequest,
    top_level_workflow: TopLevelWorkflow = Depends(
        Provide[Container.top_level_workflow]
    ),
):
    prompt = """
    INSTRUCTIONS:
    - Perform a multi-step procedure to report data based on the user question.
    - The procedure consists of the following tasks executed only by the team responsible for reporting data.
        1. Answer the user question accurately: {question}
    """
    if not data_reporting_request.format_instructions:
        input_message = prompt.format(question=data_reporting_request.question)
    else:
        # This creates a string similar to what JsonOutputParser().get_format_instructions() would produce.
        format_instructions = json.dumps(
            data_reporting_request.format_instructions, indent=2
        )
        prompt += """
        CRITICAL RULES:
        - Your final answer MUST be a JSON object that strictly adheres to the following JSON schema. 
        - Do not include any other text or explanations outside of the JSON object itself.\n
        ```json
        {format_instructions}
        ```
        """
        print(f"prompt: {prompt}")
        input_message = prompt.format(
            question=data_reporting_request.question,
            format_instructions=format_instructions,
        )

    result = await top_level_workflow.run(input_message=input_message)
    logger.info(f"Final result: {result}")

    content = result[-1].content
    try:
        clean_json_string = content.strip("`\n").lstrip("json\n").rstrip("`")
        data_object = json.loads(clean_json_string)
        return DataReportingResponse(answer=data_object)
    except json.JSONDecodeError:
        logger.info("The content is not valid JSON.")

    return DataReportingResponse(answer=content)
