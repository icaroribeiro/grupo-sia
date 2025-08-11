import os
import zipfile
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.core_logic_layer.logging import logger


class UnzipFilesFromZipArchiveInput(BaseModel):
    file_path: str = Field(..., description="Path to the ZIP file.")
    destination_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )


class UnzipFilesFromZipArchiveTool(BaseTool):
    name: str = "unzip_files_from_zip_archive_tool"
    description: str = "Unzip files from ZIP archive to a destination directory."
    args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

    def _run(self, file_path: str, destination_dir_path: str) -> str | ToolOutput:
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
            # return ToolOutput(
            #     message="succeed",
            #     result=[file.replace("\\", "/") for file in extracted_files],
            # )
            return (
                f"file_paths = {[file.replace('\\', '/') for file in extracted_files]}"
            )
        except Exception as error:
            message = f"Error: {str(error)}"
            logger.error(message)
            return ToolOutput(status="failed", result=None)

    async def _arun(
        self, file_path: str, destination_dir_path: str
    ) -> str | ToolOutput:
        return self._run(file_path=file_path, destination_dir_path=destination_dir_path)
