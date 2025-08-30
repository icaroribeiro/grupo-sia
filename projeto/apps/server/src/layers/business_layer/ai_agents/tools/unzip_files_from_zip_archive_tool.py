import os
import zipfile
from typing import Type
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langgraph.types import Command
from typing import Annotated

# from src.layers.business_layer.ai_agents.models.tool_output_model import (
#     ToolOutputModel,
# )
from langchain_core.tools import InjectedToolCallId
from src.layers.core_logic_layer.logging import logger


class UnzipFilesFromZipArchiveInput(BaseModel):
    file_path: str = Field(..., description="Path to the ZIP archive.")
    destination_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class UnzipFilesFromZipArchiveTool(BaseTool):
    name: str = "unzip_files_from_zip_archive_tool"
    description: str = "Unzip files from ZIP archive to a destination directory."
    args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

    def _run(
        self, file_path: str, destination_dir_path: str, tool_call_id: str
    ) -> Command:
        logger.info(f"Calling {self.name}...")
        try:
            os.makedirs(destination_dir_path, exist_ok=True)
            extracted_files = []
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(destination_dir_path)
                extracted_files = [
                    os.path.join(destination_dir_path, name)
                    for name in zip_ref.namelist()
                    if not name.endswith("/")
                ]
            # return ToolOutputModel(
            #     status=Status.SUCCEED,
            #     result=[file.replace("\\", "/") for file in extracted_files],
            # )
            tool_output_message = ToolMessage(
                content=str(extracted_files),
                tool_call_id=tool_call_id,
            )
            return Command(
                update={
                    "csv_file_paths": [
                        file.replace("\\", "/") for file in extracted_files
                    ],
                    "messages": [tool_output_message],
                }
            )
        except Exception as error:
            message = f"Error: {str(error)}"
            logger.error(message)
            # return ToolOutputModel(status=Status.FAILED, result=None)
            return Command(update={"extracted_csv_files": [], "messages": [message]})

    async def _arun(
        self, file_path: str, destination_dir_path: str, tool_call_id: str
    ) -> Command:
        return self._run(
            file_path=file_path,
            destination_dir_path=destination_dir_path,
            tool_call_id=tool_call_id,
        )
