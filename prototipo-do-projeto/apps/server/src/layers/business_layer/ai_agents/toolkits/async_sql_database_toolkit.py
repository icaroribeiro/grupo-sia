from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from src.layers.business_layer.ai_agents.tools.async_query_sql_database_tool import (
    AsyncQuerySQLDatabaseTool,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


class AsyncSQLDatabaseToolkit(BaseModel):
    def __init__(self, llm: BaseChatModel, postgresdb: PostgresDB):
        self.__llm = llm
        self.__postgresdb = postgresdb

    def get_tools(self) -> list[BaseTool]:
        return [
            AsyncQuerySQLDatabaseTool(postgresdb=self.__postgresdb, llm=self.__llm),
            InfoSQLDatabaseTool(db=self.__postgresdb),
            ListSQLDatabaseTool(db=self.__postgresdb),
            QuerySQLCheckerTool(db=self.__postgresdb, llm=self.__llm),
        ]
