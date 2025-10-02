import os
import zipfile
from typing import Annotated, Type

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class UnzipZipFileToolInput(BaseModel):
    file_path: str = Field(default=..., description="Path to the ZIP file.")
    destination_dir_path: str = Field(
        default=..., description="Path to the destination directory."
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class UnzipZipFileTool(BaseTool):
    name: str = "unzip_zip_file_tool"
    description: str = "Unzip ZIP file to a destination directory."
    args_schema: Type[BaseModel] = UnzipZipFileToolInput

    def _run(
        self, file_path: str, destination_dir_path: str, tool_call_id: str
    ) -> ToolMessage:
        logger.info(f"Calling {self.name}...")
        try:
            os.makedirs(destination_dir_path, exist_ok=True)
            extracted_file_paths = []
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(destination_dir_path)
                extracted_file_paths = [
                    os.path.join(destination_dir_path, name)
                    for name in zip_ref.namelist()
                    if not name.endswith("/")
                ]
            csv_file_paths = [file.replace("\\", "/") for file in extracted_file_paths]
            logger.info(f"ZIP file unzipped resulting in file paths: {csv_file_paths}")
            return ToolMessage(
                content=f"csv_file_paths:{csv_file_paths}",
                name=self.name,
                tool_call_id=tool_call_id,
            )
        except Exception as error:
            message = f"{str(error)}"
            logger.error(message)
            return ToolMessage(
                content="csv_file_paths:[]",
                name=self.name,
                tool_call_id=tool_call_id,
            )

    async def _arun(
        self, file_path: str, destination_dir_path: str, tool_call_id: str
    ) -> ToolMessage:
        return self._run(
            file_path=file_path,
            destination_dir_path=destination_dir_path,
            tool_call_id=tool_call_id,
        )
