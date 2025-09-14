import os

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)
from src.layers.core_logic_layer.dependencies.dependencies import Dependencies
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.app_settings import AppSettings
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
async def data_ingestion(
    response: Response,
    file: UploadFile = File(...),
    app_settings: AppSettings = Depends(Dependencies.get_app_settings),
    top_level_workflow: TopLevelWorkflow = Depends(Dependencies.get_top_level_workflow),
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

    dir_path = app_settings.upload_data_dir_path
    extracted_dir_path = app_settings.upload_extracted_data_dir_path
    ingestion_dir_path = app_settings.ingestion_data_dir_path
    file_path = os.path.join(dir_path, file.filename)
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as error:
        message = f"Error: Failed to write file {file.filename} in {dir_path}: {error}"
        logger.error(message)
        raise ServerError(message=message)

    data_ingestion_response: DataIngestionResponse = DataIngestionResponse()
    try:
        prompt = """
        INSTRUCTIONS:
        - Perform a multi-step procedure to insert invoice and invoice items records into database.
        - The procedure consists of the following tasks directed to data ingestion team:
            1. Unzip files from ZIP archive located at '{file_path}' to the directory '{extracted_dir_path}'.
            2. Map extracted CSV files located at '{extracted_dir_path}' to database ingestion arguments to the directory '{ingestion_dir_path}'.
            3. Insert records from ingestion arguments into database.
        CRITICAL RULES:
        - DO NOT proceed with one task if the previous only was not completed.
        - DO NOT perform handoffs in parallel.
        """
        input_message = prompt.format(
            file_path=file_path,
            extracted_dir_path=extracted_dir_path,
            ingestion_dir_path=ingestion_dir_path,
        )

        result = await top_level_workflow.run(input_message=input_message)
        logger.info(f"API request final result: {result}")
        content = result[-1].content
        logger.info(f"API request final result content: {content}")
        return data_ingestion_response
    except Exception as error:
        message = f"Error: Failed to ingest data into database: {error}"
        logger.error(message)
        data_ingestion_response = DataIngestionResponse(status="UnIngested")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return data_ingestion_response
