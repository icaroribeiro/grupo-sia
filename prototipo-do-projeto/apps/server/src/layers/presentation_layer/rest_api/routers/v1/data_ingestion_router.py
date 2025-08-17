import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
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
    data_ingestion_workflow: DataIngestionWorkflow = Depends(
        Provide[Container.data_ingestion_workflow]
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

    dir_path = config["app_settings"].uploads_data_dir_path
    file_path = os.path.join(dir_path, file.filename)
    destination_dir_path = f"{dir_path}/extracted"
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as error:
        message = f"Error: Failed to write file {file.filename} in {dir_path}: {error}"
        logger.error(message)
        raise ServerError(message=message)

    prompt = """
    INSTRUCTIONS:
    Perform the following tasks in the order listed.
    Each task is dependent on the successful completion of the previous one.
    1. Unzip the file located at '{file_path}' to the directory '{destination_dir_path}'.
    2. Map the list of paths of extracted CSV files to ingestion arguments.
    3. Insert ingestion args mapped from extracted CSV files into a Postgres database.
    CRITICAL RULES:
    Execute these tasks ONE AT A TIME.
    DO NOT begin the next task until the current one is fully completed and verified.
    """
    input_message = prompt.format(
        file_path=file_path, destination_dir_path=destination_dir_path
    )

    result = await data_ingestion_workflow.run(input_message=input_message)
    logger.info(f"result: {result}")
    # answer: str = result[-1].content
    # logger.info(f"Final result: {answer}")
    return DataIngestionResponse(status="Loaded")
