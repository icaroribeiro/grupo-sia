from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.tools import ToolException
from sqlalchemy import text

from src.core.logging import logger
from src.infra.db.postgresql import PostgreSQL


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
