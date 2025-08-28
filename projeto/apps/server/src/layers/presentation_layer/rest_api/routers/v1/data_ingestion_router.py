import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow_2 import (
    DataIngestionWorkflow2,
)
from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.data_ingestion_schema import (
    DataIngestionResponse,
)
from src.server_error import ServerError

router = APIRouter()


@router.post(
    "/data-ingestion",
    response_model=DataIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
@inject
async def data_ingestion(
    response: Response,
    file: UploadFile = File(...),
    config: dict = Depends(Provide[Container.config]),
    data_ingestion_workflow: DataIngestionWorkflow2 = Depends(
        Provide[Container.data_ingestion_workflow_2]
    ),
    top_level_workflow: TopLevelWorkflow = Depends(
        Provide[Container.top_level_workflow]
    ),
):
    if file.content_type != "application/zip":
        message = "Error: Failed to check if Content-Type in request header is "
        "defined as 'application/zip'"
        logger.error(message)
        raise ServerError(
            message=message,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only ZIP files are allowed",
        )

    dir_path = config["app_settings"].upload_data_dir_path
    file_path = os.path.join(dir_path, file.filename)
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as error:
        message = f"Error: Failed to write file {file.filename} in {dir_path}: {error}"
        logger.error(message)
        raise ServerError(message=message)

    extracted_dir_path = f"{dir_path}/extracted"
    ingestion_dir_path = config["app_settings"].ingestion_data_dir_path
    prompt = """
    INSTRUCTIONS:     
    - Perform a multi-step data ingestion procedure to insert records into database.
    - The data ingestion consists of three stages executed by ONLY the data ingestion team, and you must delegate the work to a single agent for each stage in the order listed.
    - The stages are:
        1. Unzip files from ZIP Archive located at '{file_path}' to the directory '{extracted_dir_path}'.
        2. Map CSVs to Ingestion Arguments in the directory '{ingestion_dir_path}'.
    - You must always delegate to ONE AGENT AT TIME.
    - You must wait for the result of the current agent's task before moving to the next stage.
    CRITICAL RULES:
    - Do NOT ask for additional input. All tasks are fully defined.
    - Each stage is dependent on the successful completion of the previous one.
    - DO NOT begin the next stage until the current one is fully completed and verified.
    """
    input_message = prompt.format(
        file_path=file_path,
        extracted_dir_path=extracted_dir_path,
        ingestion_dir_path=ingestion_dir_path,
    )

    # result = await data_ingestion_workflow.run(input_message=input_message)
    result = await top_level_workflow.run(input_message=input_message)
    logger.info(f"result: {result}")
    # answer: str = result[-1].content
    # logger.info(f"Final result: {answer}")
    content = result[-1].content
    return DataIngestionResponse(status=content)

    # prompt = """
    # INSTRUCTIONS:
    # - Perform a multi-step data ingestion procedure to insert records into database.
    # - The data ingestion consists of three stages, and you must delegate the work to a single agent for each stage in the order listed.
    # - The stages are:
    # 1. Unzip files from ZIP Archive located at '{file_path}'
    #     - You MUST send files to the destionation directory '{extracted_dir_path}'
    #     - You MUST inform the result of this stage to the agent responsible for the next stage.
    # 2. Map extracted CSV files to ingestion arguments
    #     - You MUST save files in destionation directory '{ingestion_dir_path}'.
    #     - You MUST inform the result of this stage to the agent responsible for the next stage.
    # 3. Insert Ingestion Arguments Into Database.
    #     - The result of this stage contains information about inserting records into the database.
    # INSTRUCTIONS:
    # - You must always pay attention to the result of a stage execution to get any data needed to perfom the next stage.
    # - You must delegate to one agent at time inside the team and inform the result of a previous tool call when needed.
    # - You must wait for the result of the current agent's task before moving to the next stage and always inform the destination directory in your request when it is necessary.
    # CRITICAL RULES:
    # - Only one team is in charge of executing all the stages.
    # - Do NOT ask for additional input. All tasks are fully defined.
    # - Each stage is dependent on the successful completion of the previous one.
    # - DO NOT begin the next stage until the current one is fully completed and verified.
    # """

    # 3. Insert Ingestion Arguments Into Database.
