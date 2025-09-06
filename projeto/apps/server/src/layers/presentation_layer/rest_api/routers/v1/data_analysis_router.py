import json

from fastapi import APIRouter, Depends, Response, status

from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)
from src.layers.core_logic_layer.dependencies.dependencies import Dependencies
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
async def data_analysis(
    response: Response,
    data_analysis_request: DataAnalysisRequest,
    top_level_workflow: TopLevelWorkflow = Depends(Dependencies.get_top_level_workflow),
):
    input_message = """
    INSTRUCTIONS:
    - Perform a multi-step procedure to analyze data based on the user's question.
    - The procedure consists of the following tasks executed only by the team responsible for data analysis.
        1. Analyze the user's question accurately: {question}
    """
    if not data_analysis_request.format_instructions:
        input_message = input_message.format(question=data_analysis_request.question)
    else:
        # This creates a string similar to what JsonOutputParser().get_format_instructions() would produce.
        format_instructions = json.dumps(
            data_analysis_request.format_instructions, indent=2
        )
        input_message += """
        2. Format the final answer to the user's question as a JSON object that strictly adheres to the following schema:
        ```json
        {format_instructions}
        ```
        CRITICAL RULES:
        - A JSON object must always be returned, not a string of a JSON object.
        - DO NOT include any other text or explanations outside of the JSON object itself.
        """
        input_message = input_message.format(
            question=data_analysis_request.question,
            format_instructions=format_instructions,
        )
    result = await top_level_workflow.run(input_message=input_message)
    logger.info(f"API request final result: {result}")
    content = result[-1].content
    try:
        clean_json_string = content.strip("`\n").lstrip("json\n").rstrip("`")
        data_object = json.loads(clean_json_string)
        return DataAnalysisResponse(answer=data_object)
    except json.JSONDecodeError:
        logger.info("The content is not valid JSON.")
    return DataAnalysisResponse(answer=content)
