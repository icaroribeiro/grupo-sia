from typing import Any, Type

import pandas as pd
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.models.base_model import (
    BaseModel as SQLAlchemyBaseModel,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB
from langchain_core.messages import ToolMessage


class InsertRecordsIntoDatabaseInput(BaseModel):
    ingestion_args_list: list[dict[str, str]] = Field(
        ..., description="List of ingestion arguments."
    )


class InsertRecordsIntoDatabaseTool(BaseTool):
    name: str = "insert_records_into_database_tool"
    description: str = (
        "Insert ingestion args into Postgres database using SQLALchemy ORM."
    )
    postgresdb: PostgresDB
    sqlalchemy_model_by_table_name: dict[str, Type[SQLAlchemyBaseModel]]
    ingestion_config_dict: dict[int, dict[str, Any]]
    args_schema: Type[BaseModel] = InsertRecordsIntoDatabaseInput

    def __init__(
        self,
        postgresdb: PostgresDB,
        sqlalchemy_model_by_table_name: dict[str, Type[SQLAlchemyBaseModel]],
        ingestion_config_dict: dict[int, dict[str, Any]],
    ):
        super().__init__(
            postgresdb=postgresdb,
            sqlalchemy_model_by_table_name=sqlalchemy_model_by_table_name,
            ingestion_config_dict=ingestion_config_dict,
        )
        self.postgresdb = postgresdb
        self.sqlalchemy_model_by_table_name = sqlalchemy_model_by_table_name
        self.ingestion_config_dict = ingestion_config_dict

    async def _arun(
        self, ingestion_args_list: list[dict[str, str]], tool_call_id: str
    ) -> ToolMessage:
        logger.info(f"Calling {self.name}...")
        count_map: dict[str, int] = dict()
        try:
            count_map: dict[str, int] = dict()
            async with self.postgresdb.async_session() as async_session:
                for index, ingestion_args in enumerate(ingestion_args_list):
                    table_name = ingestion_args["table_name"]
                    file_path = ingestion_args["file_path"]
                    if table_name not in self.sqlalchemy_model_by_table_name:
                        logger.error(f"Error: Invalid table name '{table_name}'")
                        return ToolMessage(
                            content=f"result=Table name {table_name} is invalid.",
                            name=self.name,
                            tool_call_id=tool_call_id,
                        )
                    model_class = self.sqlalchemy_model_by_table_name[table_name]
                    if table_name not in count_map:
                        count_map[table_name] = 0

                    df: pd.DataFrame = pd.DataFrame()
                    try:
                        df = pd.read_csv(
                            file_path,
                            dtype=self.ingestion_config_dict[index][
                                "model_fields_to_dtypes"
                            ],
                        )
                    except FileNotFoundError as error:
                        message = f"Error: Failed to find file at {file_path}: {error}"
                        logger.error(message)
                        return ToolMessage(
                            content="result=None",
                            name=self.name,
                            tool_call_id=tool_call_id,
                        )
                    except UnicodeDecodeError as error:
                        message = f"Error: Failed to decode data from file {file_path}: {error}"
                        logger.error(message)
                        return ToolMessage(
                            content="result=None",
                            name=self.name,
                            tool_call_id=tool_call_id,
                        )
                    except Exception as error:
                        message = f"Error: Failed to read file {file_path}: {error}"
                        logger.error(message)
                        return ToolMessage(
                            content="result=None",
                            name=self.name,
                            tool_call_id=tool_call_id,
                        )

                    for _, row in df.iterrows():
                        try:
                            model_data = {}
                            for doc_field_info in self.ingestion_config_dict[index][
                                "csv_columns_to_model_fields"
                            ].values():
                                field_name = doc_field_info["field"]
                                value = row.get(field_name)
                                if value is pd.NA or pd.isna(value):
                                    value = None
                                model_data[field_name] = value
                            model = model_class.from_data(data=model_data)
                            async_session.add(model)
                            # Flush sends the data to the DB to catch errors early
                            # but does NOT commit the transaction.
                            await async_session.flush()
                            count_map[table_name] += 1
                        except IntegrityError:
                            # This error means the record already exists (e.g., duplicate primary key).
                            # We must rollback this specific failed transaction chunk.
                            await async_session.rollback()
                            logger.warning(
                                f"Warning: Duplicate record skipped in table '{table_name}'. Continuing."
                            )
                            # Continue to the next record.
                            continue
                        except Exception as error:
                            # For any other error during record processing, rollback and fail hard.
                            await async_session.rollback()
                            logger.error(
                                f"Error processing record for {table_name}: {error}"
                            )
                            return ToolMessage(
                                content=f"result={str(error)}.",
                                name=self.name,
                                tool_call_id=tool_call_id,
                            )

                # === 2. Final Commit (Moved Outside the Loop) ===
                # Commit the entire transaction only after all records
                # from all tables have been successfully processed.
                await async_session.commit()
                logger.info("Success: All records from all tables have been committed.")

        except Exception as error:
            # Catch any other unexpected errors during the session.
            logger.error(f"An unexpected error occurred in the tool: {error}")
            return ToolMessage(
                content=f"result={str(error)}.",
                name=self.name,
                tool_call_id=tool_call_id,
            )

        if not any(count_map.values()):
            logger.warning("Warning: No new records were available to insert.")
            return ToolMessage(
                content="result=No new records inserted.",
                name=self.name,
                tool_call_id=tool_call_id,
            )

        total_count = sum(count_map.values())
        for model_name, count in count_map.items():
            if count > 0:
                logger.info(
                    f"Success: {count} record(s) inserted into {model_name} table"
                )

        return ToolMessage(
            content=f"result=Successfully inserted {total_count} records.",
            name=self.name,
            tool_call_id=tool_call_id,
        )

    def _run(self, ingestion_args_list: list[dict[str, str]]) -> ToolMessage:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
