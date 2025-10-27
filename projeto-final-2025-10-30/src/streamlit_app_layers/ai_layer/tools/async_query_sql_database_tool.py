from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from sqlalchemy import text

from src.streamlit_app_layers.core_layer.logging import logger
from src.streamlit_app_layers.data_access_layer.db.postgresql import PostgreSQL
from langchain_core.tools import ToolException


class AsyncQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    def __init__(self, postgresql: PostgreSQL):
        super().__init__(db=postgresql)
        self.name = "async_query_sql_database_tool"
        self.db = postgresql

    async def _arun(self, query: str) -> str:
        logger.info(f"Calling {self.name}...")
        try:
            async with self.db.async_session() as async_session:
                result = await async_session.execute(text(query))
                return str([dict(row) for row in result.mappings().all()])

        except Exception as error:
            message = f"Error executing SQL query: {str(error)}"
            logger.error(message)
            raise ToolException(message)
