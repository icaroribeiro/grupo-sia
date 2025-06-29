import os
import zipfile

from src.infra.logging import logger
from crewai.tools import BaseTool


class UnzipFileTool(BaseTool):
    name: str = "Unzip File Tool"
    description: str = """
        Extracts all CSV files from a ZIP archive to a specified directory.

        Arguments:
            zip_path (str): The ZIP archive path.
            csv_dir_path (str): The extracted CSV files directory path.
    """

    def _run(self, zip_path: str, csv_dir_path: str) -> list[str]:
        if not os.path.exists(zip_path):
            err = f"Error: Zip file not found at {zip_path}"
            logger.error(err)
            return [err]

        try:
            os.makedirs(csv_dir_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(csv_dir_path)

                csv_file_paths = [
                    os.path.join(csv_dir_path, f)
                    for f in os.listdir(csv_dir_path)
                    if f.endswith(".csv")
                ]

                if not csv_file_paths:
                    err = f"Error: No CSV files found in ZIP at {csv_dir_path}."
                    logger.error(err)
                    return [err]

                logger.info(
                    f"{zip_path} file successfully unzipped: {','.join(csv_file_paths)}"
                )
                return csv_file_paths
        except zipfile.BadZipFile as err:
            err = f"Error: {zip_path} file is not a valid ZIP file: {err}"
            logger.error(err)
            return [err]
        except Exception as err:
            err = f"Error: {zip_path} file not unzipping: {err}"
            logger.error(err)
            return [err]
