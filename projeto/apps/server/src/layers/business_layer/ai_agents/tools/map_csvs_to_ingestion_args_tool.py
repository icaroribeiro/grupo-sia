import os
import re
from typing import Any, Type
import pandas as pd
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from src.layers.business_layer.ai_agents.models.tool_output import Status, ToolOutput
from src.layers.core_logic_layer.logging import logger


class MapCSVsToIngestionArgsInput(BaseModel):
    file_paths: list[str] = Field(
        ..., description="List of paths of extracted CSV files."
    )
    destination_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )


class MapCSVsToIngestionArgsTool(BaseTool):
    name: str = "map_csvs_to_ingestion_args_tool"
    description: str = (
        "Map a list of paths of extracted CSV files to a list of ingestion arguments."
    )
    ingestion_config_dict: dict[int, dict[str, Any]]
    args_schema: Type[BaseModel] = MapCSVsToIngestionArgsInput

    def __init__(
        self,
        ingestion_config_dict: dict[int, dict[str, Any]],
    ):
        super().__init__(
            ingestion_config_dict=ingestion_config_dict,
        )
        self.ingestion_config_dict = ingestion_config_dict

    def _run(self, file_paths: list[str], destination_dir_path: str) -> ToolOutput:
        logger.info(f"Calling {self.name}...")
        try:
            ingestion_args_list: list[dict[str, str]] = list()
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                for _, ingestion_config in self.ingestion_config_dict.items():
                    if re.match(
                        rf"\d{{6}}_{ingestion_config['file_suffix']}\.csv$", file_name
                    ):
                        df: pd.DataFrame = pd.DataFrame()
                        try:
                            df = pd.read_csv(
                                file_path,
                                encoding="latin1",
                                sep=";",
                            )
                        except FileNotFoundError as error:
                            message = (
                                f"Error: Failed to find file at {file_path}: {error}"
                            )
                            logger.error(message)
                            return ToolOutput(status=Status.FAILED, result=None)
                        except UnicodeDecodeError as error:
                            message = f"Error: Failed to decode data from file {file_path}: {error}"
                            logger.error(message)
                            return ToolOutput(status=Status.FAILED, result=None)
                        except Exception as error:
                            message = f"Error: Failed to read file {file_path}: {error}"
                            logger.error(message)
                            return ToolOutput(status=Status.FAILED, result=None)

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
                                message = f"Error: Failed to process row {index + 1} from {file_path}: {error}"
                                logger.error(message)
                                continue
                        df_concatenated.to_csv(
                            path_or_buf=os.path.join(
                                destination_dir_path, f"{file_name}"
                            )
                        )
                        ingestion_args_list.append(
                            {
                                "table_name": ingestion_config["table_name"],
                                "file_path": os.path.join(
                                    destination_dir_path, f"{file_name}"
                                ),
                            }
                        )
            return ToolOutput(status=Status.SUCCEED, result=ingestion_args_list)
        except Exception as error:
            message = f"Error: {str(error)}"
            logger.error(message)
            return ToolOutput(status=Status.FAILED, result=None)

    async def _arun(
        self, file_paths: list[str], destination_dir_path: str
    ) -> ToolOutput:
        return self._run(
            file_paths=file_paths, destination_dir_path=destination_dir_path
        )
