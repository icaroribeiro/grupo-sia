from typing import Any, Dict, List, Tuple, Type

import pandas as pd
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from src.core.logging import logger
from src.infra.db.models.base_model import (
    BaseModel as SQLAlchemyBaseModel,
)
from src.infra.db.postgresql import PostgreSQL


class InsertRecordsIntoDatabaseInput(BaseModel):
    ingestion_args_list: List[Dict[str, str]] = Field(
        ...,
        description="List of ingestion arguments, where each dict contains 'table_name' and 'file_path'.",
    )


class InsertRecordsIntoDatabaseTool(BaseTool):
    name: str = "insert_records_into_database_tool"
    description: str = (
        "Insert ingestion args (containing file path and table name) into Postgres "
        "database using SQLAlchemy ORM. Skips duplicate records but fails on other errors."
    )
    postgresql: PostgreSQL
    sqlalchemy_model_by_table_name: Dict[str, Type[SQLAlchemyBaseModel]]
    ingestion_config_dict: Dict[int, Dict[str, Any]]
    args_schema: Type[BaseModel] = InsertRecordsIntoDatabaseInput
    response_format: str = "content_and_artifact"

    def __init__(
        self,
        postgresql: PostgreSQL,
        sqlalchemy_model_by_table_name: Dict[str, Type[SQLAlchemyBaseModel]],
        ingestion_config_dict: Dict[int, Dict[str, Any]],
    ):
        super().__init__(
            postgresql=postgresql,
            sqlalchemy_model_by_table_name=sqlalchemy_model_by_table_name,
            ingestion_config_dict=ingestion_config_dict,
        )
        self.postgresql = postgresql
        self.sqlalchemy_model_by_table_name = sqlalchemy_model_by_table_name
        self.ingestion_config_dict = ingestion_config_dict

    async def _arun(
        self,
        ingestion_args_list: List[Dict[str, str]],
    ) -> Tuple[str, Dict[str, int]]:
        logger.info(f"Calling {self.name}...")

        count_map: Dict[str, int] = {}
        total_inserted_count: int = 0

        try:
            async with self.postgresql.async_session() as async_session:
                for index, ingestion_args in enumerate(ingestion_args_list):
                    table_name = ingestion_args["table_name"]
                    file_path = ingestion_args["file_path"]

                    if table_name not in self.sqlalchemy_model_by_table_name:
                        message = f"Error: Invalid table name '{table_name}' found in ingestion arguments."
                        logger.error(message)
                        raise ToolException(message)

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
                    except (FileNotFoundError, UnicodeDecodeError, Exception) as error:
                        message = f"Error reading file {file_path}: {error.__class__.__name__}: {error}"
                        logger.error(message)
                        raise ToolException(message) from error

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
                            await (
                                async_session.flush()
                            )  # Tenta enviar para o DB para pegar IntegrityError cedo
                            count_map[table_name] += 1
                            total_inserted_count += 1

                        except IntegrityError:
                            await async_session.rollback()
                            logger.warning(
                                f"Warning: Duplicate record skipped in table '{table_name}'. Continuing."
                            )
                            continue

                        except (SQLAlchemyError, Exception) as error:
                            await async_session.rollback()
                            message = f"Critical Error processing record for {table_name}: {error.__class__.__name__}: {error}"
                            logger.error(message)
                            raise ToolException(message) from error

                await async_session.commit()
                logger.info(
                    f"Success: All {total_inserted_count} records committed across all tables."
                )

        except ToolException:
            raise

        except Exception as error:
            message = f"An unexpected critical error occurred: {error.__class__.__name__}: {error}"
            logger.error(message)
            raise ToolException(message) from error

        if total_inserted_count == 0:
            content = "Warning: No new records were inserted into the database. All were skipped (duplicates or empty data)."
        else:
            content = f"Successfully inserted {total_inserted_count} new records into the database across {len(count_map)} tables."

        artifact = count_map

        return content, artifact

    def _run(
        self,
        ingestion_args_list: List[Dict[str, str]],
    ) -> Tuple[str, Dict[str, int]]:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
