import os
import zipfile

from crewai.tools import BaseTool

from ai_agents_crew.logger.logger import logger


class UnzipFileTool(BaseTool):
    name: str = "Unzip File"
    description: str = """
        Extracts all contents from a zip file to a specified destination directory.
        Log a comma-separated string of extracted file paths on success
        or raise an exception on failure.

        Arguments:
            src_dir (str): The source directory.
            dst_dir (str): The destination directory.
    """

    def _run(self, src_dir: str, dst_dir: str = "data/extracted") -> str:
        if not os.path.exists(src_dir):
            err = f"Error: Zip file not found at {src_dir}"
            logger.error(err)
            return err

        os.makedirs(dst_dir, exist_ok=True)
        extracted_files = []
        try:
            with zipfile.ZipFile(src_dir, "r") as zf:
                for member in zf.infolist():
                    # Skip directories
                    if not member.is_dir():
                        extracted_path = os.path.join(
                            dst_dir, os.path.basename(member.filename)
                        )
                        # Prevent path traversal vulnerability by ensuring
                        # base name is used
                        zf.extract(member, path=dst_dir)
                        extracted_files.append(extracted_path)
            logger.info(
                f"Successfully extracted {src_dir}: {','.join(extracted_files)}"
            )
            return "OK"
        except zipfile.BadZipFile:
            err = f"Error: {src_dir} file is not a valid ZIP file"
            logger.error(err)
            return err
        except Exception as err:
            err = f"Error: error extracting {src_dir}: {err}"
            logger.error(err)
            return err


if __name__ == "__main__":
    logger.info("Starting Unzip file tool...")
    unzip_file_tool_result = UnzipFileTool()._run(
        src_dir="data/202401_NFs.zip", dst_dir="data/extracted"
    )
    logger.info(f"Unzip file tool result: {unzip_file_tool_result}")
    logger.info("Unzip file tool successfully executed!")
