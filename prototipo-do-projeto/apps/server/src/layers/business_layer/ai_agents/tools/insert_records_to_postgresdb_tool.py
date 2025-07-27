from typing import Tuple, Type, Union
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.postgresdb_settings import PostgresDBSettings
from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import InvoiceModel
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class InsertRecordsToPostgresDBInput(BaseModel):
    """Input schema for InsertRecordsToPostgresDBTool."""

    models_dict: dict[
        Tuple[int, str], list[Type[InvoiceModel], Type[InvoiceItemModel]]
    ] = Field(..., description="Dictionary of SQlAlchemy model classes.")


class InsertRecordsToPostgresDBTool(BaseTool):
    name: str = "insert_records_to_postgresdb_tool"
    description: str = """
    Insert SQLALchemy model classes records into Postgres database using SQLALchemy ORM.
    Returns:
        Union[str, int | None]: Status message indicating success, warning or failure
        along with the total number of inserted models.
    """
    args_schema: Type[BaseModel] = InsertRecordsToPostgresDBInput

    async def _arun(
        self,
        models_dict: dict[Tuple[int, str], list[InvoiceModel, InvoiceItemModel]],
    ) -> Union[str, int | None]:
        logger.info("The InsertRecordsToPostgresDBTool call started initiating...")
        postgresdb_settings = PostgresDBSettings()
        postgresdb = PostgresDB(postgresdb_settings=postgresdb_settings)
        count_map: dict[str, int] = dict()
        try:
            async with postgresdb.async_session() as async_session:
                if len(models_dict) > 0:
                    for _, models in sorted(models_dict.items()):
                        for model in models:
                            if count_map.get(model.get_table_name(), None) is None:
                                count_map[model.get_table_name()] = 0
                            try:
                                async_session.add(model)
                                count_map[model.get_table_name()] += 1
                            except DuplicateKeyError:
                                message = "Warning: Model already exists. "
                                f"Skipping duplicate models: {model.access_key}"
                                logger.warning(message)
                                continue
                            except Exception as error:
                                await async_session.rollback()
                                message = f"Error: Failed to insert model {model} into PostgresDB: {error}"
                                logger.error(message)
                                return (message, None)

                    try:
                        await async_session.commit()
                    except Exception as error:
                        await async_session.rollback()
                        message = f"Error: Failed to commit the current transaction in progress: {error}"
                        logger.error(message)
                        return (message, None)
        except Exception as error:
            message = (
                f"Error: Failed to check if database connection is established: {error}"
            )
            logger.error(message)
            raise

        logger.info("Database closure initiating...")
        try:
            await postgresdb.close()
            message = "Success: Database closure complete."
            logger.info(message)
        except Exception as error:
            message = f"Error: Failed to close database: {error}"
            logger.error(message)
            raise Exception(message)

        if len(count_map) > 0:
            total_count: int = 0
            for model_name, count in count_map.items():
                message = f"Success: {count} models(s) inserted into {model_name} table"
                logger.info(message)
            message = (
                f"Success: Total of {total_count} models(s) inserted into PostgreDB"
            )
            return (message, total_count)
        else:
            message = "Warning: No models to insert into PostgresDB."
            logger.warning(message)
            return (message, 0)

    def _run(
        self,
        models_dict: dict[Tuple[int, str], list[InvoiceModel, InvoiceItemModel]],
    ) -> Union[str, int | None]:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
