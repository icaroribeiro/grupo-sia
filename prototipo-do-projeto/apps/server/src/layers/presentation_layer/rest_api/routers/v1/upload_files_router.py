import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from src.layers.business_layer.ai_agents.agents.data_ingestion_agent import (
    DataIngestionAgent,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.upload_files_schema import (
    UploadFileResponse,
)
from langchain_core.prompts import ChatPromptTemplate

from src.server_error import ServerError

router = APIRouter()


@router.post(
    "/upload-zip-file",
    response_model=UploadFileResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
@inject
async def upload_zip_file(
    response: Response,
    file: UploadFile = File(...),
    config: dict = Depends(Provide[Container.config]),
    data_ingestion_agent: DataIngestionAgent = Depends(
        Provide[Container.data_ingestion_agent]
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
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    """
                    Perform the following tasks:
                    1. Unzip the file located at '{file_path}' to the directory '{dir_path}/extracted' using the `unzip_file_tool`. 
                    The result is a tuple that contains a message and a list of extracted file paths.
                    
                    2. Map all extracted files from the previous step to a list of ingestion arguments using the `map_files_to_ingestion_args_tool`.
                    The result is a tuple that contains a message and a list of ingestion arguments.
                    When calling the `map_files_to_ingestion_args_tool`, use the second item from the output of the `unzip_file_tool` tool as the input.
        
                    3. List SQLAlchemy model classes from the previous step using the `map_ingestion_args_to_models_tool`.
                    The result is a tuple that contains a message and a list of ingestion arguments.
                    When calling the `map_ingestion_args_to_models_tool`, use the second item from the output of the `map_files_to_ingestion_args_tool` tool as the input.
        
                    If both steps succeed, then provide a final answer only with the list of SQLAlchemy model classes.
                    If any error occurs during either step, return an error message that explains the reason.
                    """,
                ),
            ]
        )
        formatted_content = prompt.format(file_path=file_path, dir_path=dir_path)
        agent = data_ingestion_agent.agent
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": formatted_content}]}
        )
        logger.info(f"Final output: {result['messages'][-1].content}")
    except Exception as error:
        message = f"Error: Failed to write file {file.filename} in {dir_path}: {error}"
        logger.error(message)
        raise ServerError(message=message)

    # csv_dir_path = os.path.join(zip_path, "extracted")
    # try:
    #     await crew_orchestrator.notify_data_ingestion_crew(
    #         zip_file_path=zip_file_path, csv_dir_path=csv_dir_path
    #     )
    # except Exception as error:
    #     message = f": {error}"
    #     logger.error(message)
    #     raise

    return UploadFileResponse()
