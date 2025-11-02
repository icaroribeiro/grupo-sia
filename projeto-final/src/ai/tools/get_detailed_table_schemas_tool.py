from typing import Any, Dict, List, Tuple, Type

from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.logging import logger
from src.infra.db.postgresql import PostgreSQL


class GetDetailedTableSchemasToolInput(BaseModel):
    table_names: List[str] = Field(
        ...,
        description="List of table names for which to retrieve the detailed schema (including comments).",
    )


class GetDetailedTableSchemasTool(BaseTool):
    name: str = "get_detailed_table_schemas_tool"
    description: str = (
        "Use this tool to retrieve the complete schema structure of specific tables, "
        "including all column names, their data types, and any associated comments/descriptions. "
        "This is essential for accurately mapping complex user questions to the correct columns."
    )
    postgresql: PostgreSQL
    args_schema: Type[BaseModel] = GetDetailedTableSchemasToolInput
    response_format: str = "content_and_artifact"

    def __init__(self, postgresql: PostgreSQL):
        super().__init__(postgresql=postgresql)
        self.postgresql = postgresql

    async def _arun(
        self,
        table_names: List[str],
    ) -> Tuple[str, Dict[str, Any]]:
        logger.info(f"Calling {self.name} for tables: {table_names}")

        if not table_names:
            raise ToolException("Table names list cannot be empty.")

        query = f"""
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                (
                    SELECT pg_catalog.obj_description(
                        (
                            SELECT oid FROM pg_catalog.pg_class WHERE relname = c.table_name
                        ),
                        'pg_class'
                    )
                ) AS table_comment,
                pgd.description AS column_comment
            FROM
                information_schema.columns c
            LEFT JOIN
                pg_catalog.pg_statio_all_tables AS st ON st.relname = c.table_name
            LEFT JOIN
                pg_catalog.pg_description pgd
                ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
            WHERE
                c.table_schema = 'public' 
                AND c.table_name IN ({", ".join(f"'{t}'" for t in table_names)})
            ORDER BY
                c.table_name, c.ordinal_position;
        """

        schema_data: Dict[str, Any] = {}

        try:
            async with self.postgresql.async_engine.connect() as conn:
                result = await conn.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    content = f"Warning: No schema information found for tables: {', '.join(table_names)}."
                    return content, {}

                for row in rows:
                    (
                        table_name,
                        column_name,
                        data_type,
                        table_comment,
                        column_comment,
                    ) = row

                    if table_name not in schema_data:
                        schema_data[table_name] = {
                            "table_comment": table_comment if table_comment else "N/A",
                            "columns": [],
                        }

                    schema_data[table_name]["columns"].append(
                        {
                            "column_name": column_name,
                            "data_type": data_type,
                            "comment": column_comment if column_comment else "N/A",
                        }
                    )

                formatted_schema_list = []
                for table, data in schema_data.items():
                    col_details = []
                    for col in data["columns"]:
                        col_details.append(
                            f"  - `{col['column_name']}` ({col['data_type']}): {col['comment']}"
                        )

                    formatted_schema_list.append(
                        f"### Table: {table}\n"
                        f"**Table Description:** {data['table_comment']}\n"
                        f"**Columns:**\n" + "\n".join(col_details)
                    )

                content = "Detailed Schema Recovered:\n\n" + "\n\n".join(
                    formatted_schema_list
                )

        except SQLAlchemyError as error:
            message = f"Database Error during schema retrieval: {error.__class__.__name__}: {error}"
            logger.error(message)
            raise ToolException(message) from error

        except Exception as error:
            message = f"An unexpected critical error occurred during schema retrieval: {error.__class__.__name__}: {error}"
            logger.error(message)
            raise ToolException(message) from error

        return content, schema_data

    def _run(self, table_names: List[str]) -> Tuple[str, Dict[str, Any]]:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
