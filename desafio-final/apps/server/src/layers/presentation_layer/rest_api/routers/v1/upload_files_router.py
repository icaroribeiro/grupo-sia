import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.upload_files_schema import (
    UploadFileResponse,
)
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
    # test_workflow: TestWorkflow = Depends(Provide[Container.test_workflow]),
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
        # input_message = """
        #    Generate a random number"
        # """
        # result = await test_workflow.run(input_message=input_message)
        # logger.info(f"Final output: {result['messages'][-1].content}")
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
