import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)
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

    # initial_state = {
    #     "messages": [HumanMessage(content="Start data ingestion workflow")],
    #     "next": "entry_node",
    #     "tool_output": None,
    #     "file_path": file_path,
    #     "destination_dir_path": destination_dir_path,
    # }

    # input_message = json.dumps(
    #     {
    #         "file_path": file_path,
    #         "destination_dir_path": destination_dir_path,
    #     }
    # )

    prompt = """
    Perform the following tasks in order:
    1. Unzip the file located at '{file_path}' to the directory '{destination_dir_path}' using the 'unzip_files_from_zip_archive_tool'.
    2. Map a list of paths of extracted CSV files to a dictionary of lists of ingestion arguments using the 'map_csvs_to_ingestion_args_tool'.
    3. Insert database records into database using the 'insert_records_into_database_tool'.
    """
    input_message = prompt.format(
        file_path=file_path, destination_dir_path=destination_dir_path
    )

    result = await data_ingestion_workflow.run(input_message=input_message)

    print(
        "Final Result:",
        result["messages"][-1].content,
    )

    return UploadFileResponse(status="Uploaded")

    # 2. Map a list of paths of extracted CSV files to a dictionary of ingestion arguments using the 'map_csvs_to_ingestion_args_tool'.

    # 3. Map a dictionary of ingestion arguments to a dictionary of SQLALchemy database models using the 'map_ingestion_args_to_db_models_tool'.

    # 4. Insert SQLALchemy database models into Postgres database using the 'insert_records_into_database_tool'.


#########################
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "human",
#             """
#             Perform the following tasks in order:
#             1. Unzip the file located at '{file_path}' to the directory '{dir_path}/extracted' using the 'unzip_files_from_zip_archive_tool'.
#             The output is a 'ToolOutput' object with a 'message' (status) and 'result' (list of extracted file paths or None on failure).

#             2. Use the 'ToolOutput' object 'result' field from the previous step (list of extracted file paths) as input to the 'map_csvs_to_ingestion_args_tool' to map the extracted files to a dictionary of lists of ingestion arguments.
#             The output is a 'ToolOutput' object with a 'message' (status) and 'result' (dictionary of lists of ingestion arguments or None on failure).

#             3. Use the 'ToolOutput' object 'result' field from the previous step (dictionary of lists of ingestion arguments) as input to the 'map_ingestion_args_to_db_models_tool' to map the ingestion arguments to a dictionary of SQLAlchemy models.
#             The output is a 'ToolOutput' object with a 'message' (status) and 'result' (dictionary of SQLAlchemy models or None on failure).
#             When calling the `map_ingestion_args_to_db_models_tool`, use the dictionary of lists of ingestion arguments from previous tasks where each key is a tuple.

#             If all steps succeed, return nothing but the content of 'result' field from the 'ToolOutput' object returned from the last step.
#             If any error occurs during any step, return an error message from the 'message' field of the failing tool's 'ToolOutput', explaining the reason for the failure.
#             """,
#         ),
#     ]
# )
# formatted_content = prompt.format(file_path=file_path, dir_path=dir_path)
# agent = data_ingestion_agent.agent
# result = await agent.ainvoke(
#     {"messages": [{"role": "user", "content": formatted_content}]}
# )
# logger.info(f"Final output: {result['messages'][-1].content}")
