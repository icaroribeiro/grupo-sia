from typing import Tuple, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import InvoiceModel
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class InsertModelsIntoPostgresDBInput(BaseModel):
    """Input schema for InsertModelsIntoPostgresDBTool."""

    models_dict: dict[
        Tuple[int, str], list[Type[InvoiceModel] | Type[InvoiceItemModel]]
    ] = Field(..., description="Dictionary of lists of SQlAlchemy model classes.")


class InsertModelsIntoPostgresDBTool(BaseTool):
    name: str = "insert_models_into_postgresdb_tool"
    description: str = """
    Insert SQLALchemy model classes into Postgres database using SQLALchemy ORM.
    Returns:
        ToolOutput: An object containing a status message indicating success, warning or failure
        (string) and result (total number of inserted models on success or None on failure).
    """
    postgresdb: PostgresDB
    args_schema: Type[BaseModel] = InsertModelsIntoPostgresDBInput

    def __init__(self, postgresdb: PostgresDB):
        super().__init__(postgresdb=postgresdb)
        self.postgresdb = postgresdb

    async def _arun(
        self,
        models_dict: dict[Tuple[int, str], list[InvoiceModel | InvoiceItemModel]],
    ) -> ToolOutput:
        logger.info("The InsertModelsIntoPostgresDBTool call has started...")
        count_map: dict[str, int] = dict()
        try:
            async with self.postgresdb.async_session() as async_session:
                if len(models_dict) > 0:
                    for _, models in sorted(models_dict.items()):
                        for model in models:
                            if count_map.get(model.get_table_name(), None) is None:
                                count_map[model.get_table_name()] = 0
                            try:
                                async_session.add(model)
                                count_map[model.get_table_name()] += 1
                            except IntegrityError:
                                message = "Warning: Model already exists. "
                                f"Skipping duplicate model: {getattr(model, 'access_key', 'N/A')}"
                                logger.warning(message)
                                continue
                            except Exception as error:
                                await async_session.rollback()
                                message = f"Error: Failed to insert model {model} into PostgresDB: {error}"
                                logger.error(message)
                                return ToolOutput(message=message, result=None)
                        try:
                            await async_session.commit()
                            message = f"Success: All {model.get_table_name()} table models have been committed."
                            logger.error(message)
                        except Exception as error:
                            await async_session.rollback()
                            message = f"Error: Failed to commit the current transaction in progress: {error}"
                            logger.error(message)
                            return ToolOutput(message=message, result=None)
        except Exception as error:
            message = f"Error: Failed to establish database connection: {error}"
            logger.error(message)
            return ToolOutput(message=message, result=None)

        try:
            await self.postgresdb.close()
            message = "Success: Database connection closure complete."
            logger.info(message)
        except Exception as error:
            message = f"Error: Failed to close database connection: {error}"
            logger.error(message)
            return ToolOutput(message=message, result=None)

        if len(count_map) > 0:
            total_count: int = 0
            for model_name, count in count_map.items():
                message = f"Success: {count} models(s) inserted into {model_name} table"
                logger.info(message)
            message = f"Success: Total of {total_count} models(s) inserted into Postgres database"
            logger.info("The InsertModelsIntoPostgresDBTool call has finished.")
            return ToolOutput(message=message, result=total_count)
        else:
            message = "Warning: No models to insert into Postgres database."
            logger.warning(message)
            return ToolOutput(message=message, result=0)

    def _run(
        self,
        models_dict: dict[Tuple[int, str], list[InvoiceModel | InvoiceItemModel]],
    ) -> ToolOutput:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
