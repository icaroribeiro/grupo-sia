import os
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from langchain_core.tools import BaseTool


from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.core_logic_layer.logging import logger

from pydantic import BaseModel, Field
from typing import Type


class ListFilesFromZipArchiveInput(BaseModel):
    """Input schema for ListFilesFromZipArchiveTool."""

    file_path: str = Field(..., description="Path to the ZIP file.")
    destionation_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )


class ListFilesFromZipArchiveTool(BaseTool):
    name: str = "list_files_from_zip_archive_tool"
    description: str = """
    Extracts files from ZIP archive to a destination directory.
    Returns:
        ToolOutput: An object containing a status message indicating success, warning or failure
        (string) and result (a list of paths of extracted files from ZIP archive on success or None on failure).
    """
    args_schema: Type[BaseModel] = ListFilesFromZipArchiveInput

    def _run(self, file_path: str, destionation_dir_path: str) -> ToolOutput:
        logger.info("The ListFilesFromZipArchiveTool call has started...")
        try:
            extracted_file_paths: list[str] = list()
            os.makedirs(destionation_dir_path, exist_ok=True)
            with ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(destionation_dir_path)
                for extracted_file in zip_ref.namelist():
                    extracted_file_path = os.path.join(
                        destionation_dir_path, extracted_file
                    )
                    if (
                        Path(extracted_file_path).suffix.lower() == ".csv"
                        and Path(extracted_file_path).is_file()
                    ):
                        extracted_file_paths.append(str(extracted_file_path))
            message = f"Success: ZIP file {file_path} extracted: {','.join(extracted_file_paths)}"
            logger.info(message)
            logger.info("The ListFilesFromZipArchiveTool call has finished.")
            return ToolOutput(message=message, result=extracted_file_paths)
        except BadZipFile as error:
            message = f"Error: Failed to check that {file_path} is not a valid ZIP file: {error}"
            logger.error(message)
            return ToolOutput(message=message, result=None)
        except Exception as error:
            message = f"Error: Failed to process {file_path}: {error}"
            logger.error(message)
            return ToolOutput(message=message, result=None)
        except Exception as error:
            message = f"Error: Failed to extract files from ZIP file: {error}"
            logger.eror(message)
            return ToolOutput(message=message, result=None)

    async def _arun(self, file_path: str, destionation_dir_path: str) -> ToolOutput:
        return self._run(
            file_path=file_path, destionation_dir_path=destionation_dir_path
        )
