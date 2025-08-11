from typing import Any, Hashable, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB
from src.layers.data_access_layer.postgresdb.models.base_model import (
    BaseModel as SQLAlchemyBaseModel,
)


class InsertIngestionArgsIntoPostgresDBInput(BaseModel):
    ingestion_args: list[dict[str, str | list[dict[Hashable, Any]]]] = Field(
        ..., description="List of ingestion arguments."
    )


class InsertIngestionArgsIntoDatabaseTool(BaseTool):
    name: str = "insert_ingestion_args_into_database_tool"
    description: str = (
        "Insert ingestion args into Postgres database using SQLALchemy ORM."
    )
    postgresdb: PostgresDB
    sqlalchemy_model_by_table_name: dict[str, Type[SQLAlchemyBaseModel]]
    args_schema: Type[BaseModel] = InsertIngestionArgsIntoPostgresDBInput

    def __init__(
        self,
        postgresdb: PostgresDB,
        sqlalchemy_model_by_table_name: dict[str, Type[SQLAlchemyBaseModel]],
    ):
        super().__init__(
            postgresdb=postgresdb,
            sqlalchemy_model_by_table_name=sqlalchemy_model_by_table_name,
        )
        self.postgresdb = postgresdb
        self.sqlalchemy_model_by_table_name = sqlalchemy_model_by_table_name

    async def _arun(
        self,
        ingestion_args: list[dict[str, str | list[dict[Hashable, Any]]]],
    ) -> ToolOutput:
        logger.info(f"Calling {self.name}...")
        logger.info(f"tool - ingestion_args: {ingestion_args}")
        try:
            count_map: dict[str, int] = dict()
            async with self.postgresdb.async_session() as async_session:
                for data in ingestion_args:
                    table_name = data["table_name"]
                    if count_map.get(table_name, None) is None:
                        count_map[table_name] = 0
                    records = data["records"]

                    model_class: SQLAlchemyBaseModel
                    if table_name in self.sqlalchemy_model_by_table_name:
                        model_class = self.sqlalchemy_model_by_table_name[table_name]
                    else:
                        message = f"Error: Invalid table name {table_name}"
                        logger.error(message)
                        return ToolOutput(status="failed", result=None)

                    for record in records:
                        try:
                            model = model_class.from_data(data=record)
                            async_session.add(model)
                            # Flush the session to execute the INSERT and catch IntegrityError
                            await async_session.flush()
                            count_map[model.get_table_name()] += 1
                        except IntegrityError:
                            await async_session.rollback()  # Rollback the failed record
                            message = f"Warning: Duplicate record with access_key '{getattr(model, 'access_key', 'N/A')}' skipped."
                            logger.warning(message)
                            continue
                        except Exception as error:
                            await async_session.rollback()
                            message = f"Error: Failed to insert model {model}: {error}"
                            logger.error(message)
                            return ToolOutput(status="failed", result=None)

                    try:
                        await async_session.commit()
                        message = f"Success: All {model.get_table_name()} table records have been committed."
                        logger.info(message)
                    except Exception as error:
                        await async_session.rollback()
                        message = (
                            f"Error: Failed to commit the current transaction: {error}"
                        )
                        logger.error(message)
                        return ToolOutput(status="failed", result=None)
            if len(count_map) > 0:
                total_count: int = 0
                for model_name, count in count_map.items():
                    total_count += count
                    message = (
                        f"Success: {count} record(s) inserted into {model_name} table"
                    )
                    logger.info(message)
                return ToolOutput(message="succeed", result=total_count)
            else:
                message = "Warning: No records to insert into Postgres database."
                logger.warning(message)
                return ToolOutput(status="suceeded", result=0)
        except Exception as error:
            message = f"Error: {str(error)}"
            logger.error(message)
            return ToolOutput(status="failed", result=None)

    def _run(
        self,
        ingestion_args: list[dict[str, str | list[dict[Hashable, Any]]]],
    ) -> ToolOutput:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
