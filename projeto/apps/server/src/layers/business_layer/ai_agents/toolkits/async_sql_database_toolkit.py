from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel

from src.layers.business_layer.ai_agents.tools.async_query_sql_database_tool import (
    AsyncQuerySQLDatabaseTool,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class AsyncSQLDatabaseToolkit(BaseModel):
    def __init__(self, postgresdb: PostgresDB, llm: BaseChatModel):
        self.__db = postgresdb
        self.__llm = llm

    def get_tools(self) -> list[BaseTool]:
        return [
            AsyncQuerySQLDatabaseTool(db=self.__db, llm=self.__llm),
            InfoSQLDatabaseTool(db=self.__db),
            ListSQLDatabaseTool(db=self.__db),
            QuerySQLCheckerTool(db=self.__db, llm=self.__llm),
        ]
