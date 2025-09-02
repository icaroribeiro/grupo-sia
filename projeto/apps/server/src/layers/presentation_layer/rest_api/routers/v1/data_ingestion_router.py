import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Response, UploadFile, status

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
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@inject
async def data_ingestion(
    response: Response,
    file: UploadFile = File(...),
    config: dict = Depends(Provide[Container.config]),
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
    - Perform a multi-step procedure to insert invoice and invoice items records into database.
    - The procedure consists of the following tasks executed only by the team responsible for data ingestion.
        1. Unzip files from ZIP archive located at '{file_path}' to the directory '{extracted_dir_path}'.
        2. Map extracted CSV files to database ingestion arguments to the directory '{ingestion_dir_path}'.
    """
    input_message = prompt.format(
        file_path=file_path,
        extracted_dir_path=extracted_dir_path,
        ingestion_dir_path=ingestion_dir_path,
    )

    result = await top_level_workflow.run(input_message=input_message)
    logger.info(f"API request final result: {result}")
    content = result[-1].content
    return DataIngestionResponse(status=content)

    # 3. Insert invoice and invoice item records from ingestion arguments into database.
