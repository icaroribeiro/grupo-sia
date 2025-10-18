from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Sequence
from sqlalchemy import URL
import asyncpg
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.postgresql_db_settings import (
    PostgreSQLDBSettings,
)


class PostgreSQL(SQLDatabase):
    def __init__(
        self,
        postgresql_db_settings: PostgreSQLDBSettings,
    ):
        self.postgresql_db_settings = postgresql_db_settings
        self.__sync_engine = self.__create_engine()
        self.__async_engine = self.__create_async_engine()
        self.__async_sessionmaker = async_sessionmaker(
            autocommit=False,
            bind=self.__async_engine,
            expire_on_commit=False,
        )
        super().__init__(engine=self.__sync_engine)

    def get_conn_string(self, is_async: bool = False) -> str:
        if self.postgresql_db_settings.url:
            return self.postgresql_db_settings.url

        base_driver = self.postgresql_db_settings.driver
        driver_suffix = "+asyncpg" if is_async else ""
        driver = f"{base_driver}{driver_suffix}"
        return URL.create(
            drivername=driver,
            username=self.postgresql_db_settings.user,
            password=self.postgresql_db_settings.password,
            host=self.postgresql_db_settings.host,
            port=self.postgresql_db_settings.port,
            database=self.postgresql_db_settings.db,
        ).render_as_string(hide_password=False)

    async def table_exists(self, table_name: str) -> bool:
        conn = None
        try:
            conn = await asyncpg.connect(dsn=self.get_conn_string())
            query = """
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename = $1
                );
                """
            result = await conn.fetchval(query, table_name)
            return result
        except Exception:
            return False
        finally:
            if conn:
                await conn.close()

    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        logger.info("Starting PostgreSQL async session establishment...")
        try:
            async with self.__async_sessionmaker() as async_session:
                message = "PostgreSQL async session establishment complete."
                logger.info(message)
                yield async_session
        except Exception as error:
            message = f"PostgreSQL async session establishment failed: {error}"
            logger.error(message)
            raise Exception(message)

    async def close(self):
        logger.info("Starting PostgreSQLDB closure...")
        try:
            self.__sync_engine.dispose()
            self.__sync_engine = None
            async with self.async_session() as session:
                await session.close()
            await self.__async_engine.dispose()
            self.__async_engine = None
            self.__async_sessionmaker = None
            message = "PostgreSQL closure complete."
            logger.info(message)
        except Exception as error:
            message = f"PostgreSQL closure failed: {error}"
            logger.error(message)
            raise Exception(message)

    async def run_async(
        self, command: str | Any, fetch: str = "all"
    ) -> str | Sequence[dict[str, Any]]:
        async with self.__async_sessionmaker() as async_session:
            result = await async_session.execute(command)
            if fetch == "all":
                return [dict(row) for row in result.mappings().all()]
            elif fetch == "one":
                return dict(result.mappings().first()) if result.rowcount > 0 else {}
            return str(result)

    def __create_engine(self) -> Engine:
        return create_engine(url=self.get_conn_string())

    def __create_async_engine(self) -> AsyncEngine:
        return create_async_engine(url=self.get_conn_string(is_async=True))
