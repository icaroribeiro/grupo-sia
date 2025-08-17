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
    ingestion_args_list: list[dict[str, str | list[dict[Hashable, Any]]]] = Field(
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
        ingestion_args_list: list[dict[str, str | list[dict[Hashable, Any]]]],
    ) -> ToolOutput:
        logger.info(f"Calling {self.name}...")
        count_map: dict[str, int] = dict()
        try:
            count_map: dict[str, int] = dict()
            async with self.postgresdb.async_session() as async_session:
                for ingestion_args in ingestion_args_list:
                    table_name = ingestion_args["table_name"]
                    records = ingestion_args.get("records", [])
                    if table_name not in self.sqlalchemy_model_by_table_name:
                        logger.error(f"Error: Invalid table name '{table_name}'")
                        return ToolOutput(
                            status="failed", result=f"Invalid table name: {table_name}"
                        )

                    model_class = self.sqlalchemy_model_by_table_name[table_name]
                    if table_name not in count_map:
                        count_map[table_name] = 0

                    for record in records:
                        try:
                            model = model_class.from_data(data=record)
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
                            return ToolOutput(status="failed", result=str(error))

                # === 2. Final Commit (Moved Outside the Loop) ===
                # Commit the entire transaction only after all records
                # from all tables have been successfully processed.
                await async_session.commit()
                logger.info("Success: All records from all tables have been committed.")

        except Exception as error:
            # Catch any other unexpected errors during the session.
            logger.error(f"An unexpected error occurred in the tool: {error}")
            return ToolOutput(status="failed", result=str(error))

        # === 3. Final Reporting ===
        if not any(count_map.values()):
            logger.warning("Warning: No new records were available to insert.")
            return ToolOutput(status="succeed", result="No new records inserted.")

        total_count = sum(count_map.values())
        for model_name, count in count_map.items():
            if count > 0:
                logger.info(
                    f"Success: {count} record(s) inserted into {model_name} table"
                )

        return ToolOutput(
            status="succeed", result=f"Successfully inserted {total_count} records."
        )

    def _run(
        self,
        ingestion_args_list: list[dict[str, str | list[dict[Hashable, Any]]]],
    ) -> ToolOutput:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
