from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.language_models import BaseChatModel
from sqlalchemy import text

from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class AsyncQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    def __init__(
        self,
        postgresdb: PostgresDB,
        chat_model: BaseChatModel,
    ):
        super().__init__(db=postgresdb, chat_model=chat_model)
        self.name = "async_query_sql_database_tool"
        self.db = postgresdb

    async def _arun(self, query: str) -> str:
        logger.info(f"Calling {self.name}...")
        try:
            async with self.db.async_session() as async_session:
                result = await async_session.execute(text(query))
                return str([dict(row) for row in result.mappings().all()])
        except Exception as error:
            message = f"Error: {str(error)}"
            logger.error(message)
            raise
