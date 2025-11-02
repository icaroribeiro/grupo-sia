import os
import re
from typing import Any, Dict, List, Tuple, Type

import pandas as pd
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from src.core.logging import logger


class MapCSVsToIngestionArgsInput(BaseModel):
    source_dir_path: str = Field(
        ...,
        description="Path to the source directory containing the extracted CSV files.",
    )
    destination_dir_path: str = Field(
        ...,
        description="Path to the destination directory where mapped files will be saved.",
    )


class MapCSVsToIngestionArgsTool(BaseTool):
    name: str = "map_csvs_to_ingestion_args_tool"
    description: str = (
        "Reads all CSV files from a source directory, maps them according to configuration, "
        "and saves the mapped files to a destination directory, returning the ingestion arguments."
    )
    ingestion_config_dict: dict[int, dict[str, Any]]
    args_schema: Type[BaseModel] = MapCSVsToIngestionArgsInput
    response_format: str = "content_and_artifact"

    def __init__(
        self,
        ingestion_config_dict: dict[int, dict[str, Any]],
    ):
        super().__init__(
            ingestion_config_dict=ingestion_config_dict,
        )
        self.ingestion_config_dict = ingestion_config_dict

    def _run(
        self, source_dir_path: str, destination_dir_path: str
    ) -> Tuple[str, List[Dict[str, str]]]:
        logger.info(f"Calling {self.name}...")
        ingestion_args: List[Dict[str, str]] = []

        try:
            if not os.path.isdir(source_dir_path):
                raise ToolException(f"Source directory not found: {source_dir_path}")

            csv_file_paths = [
                os.path.join(source_dir_path, f)
                for f in os.listdir(source_dir_path)
                if f.endswith(".csv")
                and os.path.isfile(os.path.join(source_dir_path, f))
            ]

            if not csv_file_paths:
                raise ToolException(
                    f"No CSV files found in the source directory: {source_dir_path}"
                )

            for file_path in csv_file_paths:
                file_name = os.path.basename(file_path)

                matched = False
                for _, ingestion_config in self.ingestion_config_dict.items():
                    if re.match(
                        rf"\d{{6}}_{ingestion_config['file_suffix']}\.csv$", file_name
                    ):
                        matched = True
                        df: pd.DataFrame = pd.DataFrame()

                        try:
                            df = pd.read_csv(
                                file_path,
                                encoding="latin1",
                                sep=";",
                            )
                        except (
                            FileNotFoundError,
                            UnicodeDecodeError,
                            Exception,
                        ) as error:
                            message = f"Error reading file {file_path}: {error.__class__.__name__}: {error}"
                            logger.error(message)
                            raise ToolException(message) from error

                        df_concatenated: pd.DataFrame = pd.DataFrame()

                        for index, row in df.iterrows():
                            try:
                                model_data = {}
                                for (
                                    csv_col,
                                    doc_field_info,
                                ) in ingestion_config[
                                    "csv_columns_to_model_fields"
                                ].items():
                                    field_name = doc_field_info["field"]
                                    converter = doc_field_info.get("converter")
                                    value = row.get(csv_col)

                                    if value is pd.NA or pd.isna(value):
                                        value = None

                                    if converter:
                                        try:
                                            value = converter(value)
                                        except ValueError as error:
                                            message = f"Warning: Could not convert '{value}' for field '{field_name}' in row {index + 1} of {file_path}: {error}"
                                            logger.warning(message)
                                            continue

                                    model_data[field_name] = value

                                df_concatenated = pd.concat(
                                    [df_concatenated, pd.DataFrame([model_data])],
                                    ignore_index=True,
                                )
                            except Exception as error:
                                message = f"Warning: Failed to process row {index + 1} from {file_path}: {error}"
                                logger.warning(message)
                                continue

                        output_file_path = os.path.join(destination_dir_path, file_name)
                        df_concatenated.to_csv(
                            path_or_buf=output_file_path, index=False
                        )

                        ingestion_args.append(
                            {
                                "table_name": ingestion_config["table_name"],
                                "file_path": output_file_path,
                            }
                        )
                        break

                if not matched:
                    logger.warning(
                        f"No ingestion configuration matched for file: {file_name}"
                    )

            num_args = len(ingestion_args)
            content = f"Successfully mapped {num_args} CSV files to ingestion arguments. Ready for database insertion."
            artifact = ingestion_args

            return content, artifact

        except ToolException:
            raise

        except Exception as error:
            message = f"An unexpected error occurred during CSV mapping: {str(error)}"
            logger.error(message)
            raise ToolException(message) from error

    async def _arun(
        self, source_dir_path: str, destination_dir_path: str
    ) -> Tuple[str, List[str]]:
        return self._run(
            source_dir_path=source_dir_path,
            destination_dir_path=destination_dir_path,
        )
