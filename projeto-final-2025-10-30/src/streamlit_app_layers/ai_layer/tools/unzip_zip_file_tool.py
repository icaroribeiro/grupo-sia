import os
import zipfile
from typing import Type, Tuple, List

from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from src.streamlit_app_layers.core_layer.logging import logger


class UnzipZipFileToolInput(BaseModel):
    source_dir_path: str = Field(
        default=...,
        description="Path to the ZIP file.",
    )
    destination_dir_path: str = Field(
        default=...,
        description="Path to the destination directory where CSV files be extracted.",
    )


class UnzipZipFileTool(BaseTool):
    name: str = "unzip_zip_file_tool"
    description: str = "Unzip ZIP file to a destination directory."
    args_schema: Type[BaseModel] = UnzipZipFileToolInput
    response_format: str = "content_and_artifact"

    def _run(
        self, source_dir_path: str, destination_dir_path: str
    ) -> Tuple[str, List[str]]:
        logger.info(f"Calling {self.name}...")
        logger.info(f"source_dir_path: {source_dir_path}")
        logger.info(f"destination_dir_path: {destination_dir_path}")

        try:
            os.makedirs(destination_dir_path, exist_ok=True)
            extracted_file_paths = []

            if not os.path.exists(source_dir_path):
                raise FileNotFoundError(
                    f"ZIP file not found at path: {source_dir_path}"
                )

            with zipfile.ZipFile(source_dir_path, "r") as zip_ref:
                zip_ref.extractall(destination_dir_path)

                extracted_file_paths = [
                    os.path.join(destination_dir_path, name)
                    for name in zip_ref.namelist()
                    if not name.endswith("/")
                ]

            csv_file_paths = [file.replace("\\", "/") for file in extracted_file_paths]

            logger.info(
                f"ZIP file unzipped successfully. Found {len(csv_file_paths)} files."
            )

            content = f"Successfully unzipped {len(csv_file_paths)} files to {destination_dir_path}."

            artifact = csv_file_paths

            return content, artifact

        except (FileNotFoundError, zipfile.BadZipFile, Exception) as error:
            message = f"Failed to unzip file '{source_dir_path}': {type(error).__name__} - {str(error)}"
            logger.error(message)
            raise ToolException(message)

    async def _arun(
        self, source_dir_path: str, destination_dir_path: str
    ) -> Tuple[str, List[str]]:
        return self._run(
            source_dir_path=source_dir_path,
            destination_dir_path=destination_dir_path,
        )
