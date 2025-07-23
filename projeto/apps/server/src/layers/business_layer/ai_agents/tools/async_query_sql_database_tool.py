from fastapi import Depends
from sqlalchemy import text
from dependency_injector.wiring import Provide, inject
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.language_models import BaseLanguageModel
from src.layers.core_logic_layer.container.container import Container
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class AsyncQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    @inject
    def __init__(
        self,
        db: PostgresDB = Depends(Provide[Container.postgresdb]),
        llm: BaseLanguageModel = None,
    ):
        super().__init__(db=db, llm=llm)
        self.db = db

    async def _arun(self, query: str) -> str:
        try:
            async with self.db.async_session() as session:
                result = await session.execute(text(query))
                return str([dict(row) for row in result.mappings().all()])
        except Exception as e:
            return f"Error: {str(e)}"
