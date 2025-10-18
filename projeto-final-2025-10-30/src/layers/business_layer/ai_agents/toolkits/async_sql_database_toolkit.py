from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict

from src.layers.business_layer.ai_agents.tools.async_query_sql_database_tool import (
    AsyncQuerySQLDatabaseTool,
)
from src.layers.data_access_layer.db.postgresql.postgresql import PostgreSQL


class AsyncSQLDatabaseToolkit(BaseModel):
    postgresql: PostgreSQL
    chat_model: BaseChatModel

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_tools(self) -> list[BaseTool]:
        return [
            AsyncQuerySQLDatabaseTool(postgresql=self.postgresql),
            InfoSQLDatabaseTool(db=self.postgresql),
            ListSQLDatabaseTool(db=self.postgresql),
            QuerySQLCheckerTool(db=self.postgresql, llm=self.chat_model),
        ]
