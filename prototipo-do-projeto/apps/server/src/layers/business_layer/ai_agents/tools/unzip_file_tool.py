import os
from pathlib import Path
from typing import Union
from zipfile import BadZipFile, ZipFile

from langchain_core.tools import BaseTool


from src.layers.core_logic_layer.logging import logger

from pydantic import BaseModel, Field
from typing import Type


class UnzipFileInput(BaseModel):
    """Input schema for UnzipFileTool."""

    file_path: str = Field(..., description="Path to the ZIP file.")
    destionation_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )


class UnzipFileTool(BaseTool):
    name: str = "unzip_file_tool"
    description: str = """
    Extracts files from ZIP file to a destination directory.
    Returns:
        Union[str, list[str] | None]: Status message indicating success, warning or 
        failure along with a list of extracted file paths on success or 'None' on failure.
    """
    args_schema: Type[BaseModel] = UnzipFileInput

    def _run(
        self, file_path: str, destionation_dir_path: str
    ) -> Union[str, list[str] | None]:
        logger.info("The UnzipFileTool call started initiating...")
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
            return (message, extracted_file_paths)
        except BadZipFile as error:
            message = f"Error: Failed to check that {file_path} is not a valid ZIP file: {error}"
            logger.error(message)
            return (message, None)
        except Exception as error:
            message = f"Error: Failed to process {file_path}: {error}"
            logger.error(message)
            return (message, None)
        except Exception as error:
            message = f"Error: Failed to extract files from ZIP file: {error}"
            logger.eror(message)
            return (message, None)

    async def _arun(
        self, file_path: str, destionation_dir_path: str
    ) -> Union[str, list[str] | None]:
        return self._run(
            file_path=file_path, destionation_dir_path=destionation_dir_path
        )
