# import os
# from typing import Type
# import zipfile
# from langchain_core.tools import BaseTool
# from pydantic import BaseModel, Field
# from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
# from src.layers.core_logic_layer.logging import logger


# class UnzipFilesFromZipArchiveInput(BaseModel):
#     """Input schema for UnzipFilesFromZipArchiveTool."""

#     file_path: str = Field(..., description="Path to the ZIP file.")
#     destination_dir_path: str = Field(
#         ..., description="Path to the destination directory."
#     )


# class UnzipFilesFromZipArchiveTool(BaseTool):
#     name: str = "unzip_files_from_zip_archive_tool"
#     description: str = """
#     Unzip files from ZIP archive to a destination directory.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (list of paths of extracted files from ZIP archive on success or empty list on failure).
#     """
#     args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

#     def _run(self, file_path: str, destination_dir_path: str) -> ToolOutput:
#         logger.info("The UnzipFilesFromZipArchiveTool call has started...")
#         try:
#             # Ensure the destination directory exists
#             os.makedirs(destination_dir_path, exist_ok=True)

#             # List to store extracted file paths
#             extracted_files = []

#             # Unzip the file
#             with zipfile.ZipFile(file_path, "r") as zip_ref:
#                 zip_ref.extractall(destination_dir_path)
#                 # Get the list of extracted files
#                 extracted_files = [
#                     os.path.join(destination_dir_path, name)
#                     for name in zip_ref.namelist()
#                     if not name.endswith("/")
#                 ]

#             # Normalize file paths to use forward slashes
#             extracted_files = [file.replace("\\", "/") for file in extracted_files]

#             message = f"Success: ZIP file {file_path} extracted"
#             logger.info(f"{message}: {','.join(extracted_files)}")
#             logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
#             return ToolOutput(message=message, result=extracted_files)

#         except Exception as e:
#             message = f"Error unzipping file {file_path}: {str(e)}"
#             logger.error(message)
#             logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
#             return ToolOutput(message=message, result=[])

#     async def _arun(self, file_path: str, destination_dir_path: str) -> ToolOutput:
#         return self._run(file_path=file_path, destination_dir_path=destination_dir_path)
