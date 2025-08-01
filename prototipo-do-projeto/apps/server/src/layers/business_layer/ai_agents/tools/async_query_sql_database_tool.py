from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.language_models import BaseChatModel
from sqlalchemy import text

from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class AsyncQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    def __init__(
        self,
        postgresdb: PostgresDB,
        llm: BaseChatModel = None,
    ):
        super().__init__(db=postgresdb, llm=llm)
        self.name = "async_query_sql_database_tool"
        self.db = postgresdb

    async def _arun(self, query: str) -> str:
        logger.info("The AsyncQuerySQLDatabaseTool call has started...")
        try:
            async with self.db.async_session() as async_session:
                result = await async_session.execute(text(query))
                logger.info("The AsyncQuerySQLDatabaseTool has finished.")
                return str([dict(row) for row in result.mappings().all()])
        except Exception as e:
            return f"Error: {str(e)}"
