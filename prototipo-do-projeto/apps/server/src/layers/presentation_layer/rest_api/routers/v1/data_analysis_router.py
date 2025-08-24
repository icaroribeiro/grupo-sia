import json

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.data_analysis_schema import (
    DataAnalysisRequest,
    DataAnalysisResponse,
)

router = APIRouter()


@router.post(
    "/data-analysis",
    response_model=DataAnalysisResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@inject
async def data_analysis(
    response: Response,
    data_analysis_request: DataAnalysisRequest,
    data_analysis_workflow: DataAnalysisWorkflow = Depends(
        Provide[Container.data_analysis_workflow]
    ),
    top_level_workflow: TopLevelWorkflow = Depends(
        Provide[Container.top_level_workflow]
    ),
):
    prompt = """
    INSTRUCTIONS:
    - Perform data analysis accurately and respond to the following question objectively:
    Question: {question}
    """
    if not data_analysis_request.format_instructions:
        input_message = prompt.format(question=data_analysis_request.question)
    else:
        # This creates a string similar to what JsonOutputParser().get_format_instructions() would produce.
        format_instructions = json.dumps(
            data_analysis_request.format_instructions, indent=2
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
            question=data_analysis_request.question,
            format_instructions=format_instructions,
        )
    # result = await data_analysis_workflow.run(input_message=input_message)
    result = await top_level_workflow.run(input_message=input_message)
    logger.info(f"result: {result}")
    # answer: str = result[-2].content
    # logger.info(f"Final result: {answer}")

    # content = result[-2].content
    # try:
    #     clean_json_string = content.strip("`\n").lstrip("json\n").rstrip("`")
    #     data_object = json.loads(clean_json_string)
    #     return DataAnalysisResponse(answer=data_object)
    # except json.JSONDecodeError:
    #     logger.info("The content is not valid JSON.")

    # return DataAnalysisResponse(answer=content)

    content = result[-1].content
    try:
        clean_json_string = content.strip("`\n").lstrip("json\n").rstrip("`")
        data_object = json.loads(clean_json_string)
        return DataAnalysisResponse(answer=data_object)
    except json.JSONDecodeError:
        logger.info("The content is not valid JSON.")

    return DataAnalysisResponse(answer=content)
