from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Sequence

from src.layers.core_logic_layer.settings.postgresdb_settings import (
    PostgresDBSettings,
)

from src.layers.core_logic_layer.logging import logger
from sqlalchemy import URL, Engine
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase


class PostgresDB(SQLDatabase):
    def __init__(self, postgresdb_settings: PostgresDBSettings):
        self.__sync_engine = self.__create_engine(
            postgresdb_settings=postgresdb_settings
        )
        self.__async_engine = self.__create_async_engine(
            postgresdb_settings=postgresdb_settings
        )
        self.__async_sessionmaker = async_sessionmaker(
            autocommit=False,
            bind=self.__async_engine,
            expire_on_commit=False,
        )
        super().__init__(self.__sync_engine)

    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        logger.info("PostgresDB async session establishment initiating...")
        try:
            async with self.__async_sessionmaker() as async_session:
                message = "Success: PostgresDB async session establishment complete."
                logger.info(message)
                yield async_session
        except Exception as error:
            message = f"Error: Failed to establish PostgresDB async session: {error}"
            logger.error(message)
            raise Exception(message)

    async def close(self):
        logger.info("PostgresDB closure initiating...")
        try:
            self.__sync_engine.dispose()
            self.__sync_engine = None
            async with self.async_session() as session:
                await session.close()
            await self.__async_engine.dispose()
            self.__async_engine = None
            self.__async_sessionmaker = None
            message = "Success: PostgresDB closure complete."
            logger.info(message)
        except Exception as error:
            message = f"Error: Failed to close PostgresDB: {error}"
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

    @staticmethod
    def __create_engine(postgresdb_settings: PostgresDBSettings) -> Engine:
        return create_engine(
            url=URL.create(
                drivername=postgresdb_settings.driver,
                username=postgresdb_settings.username,
                password=postgresdb_settings.password,
                host=postgresdb_settings.host,
                port=postgresdb_settings.port,
                database=postgresdb_settings.database,
            )
        )

    @staticmethod
    def __create_async_engine(postgresdb_settings: PostgresDBSettings) -> AsyncEngine:
        return create_async_engine(
            url=URL.create(
                drivername=f"{postgresdb_settings.driver}+asyncpg",
                username=postgresdb_settings.username,
                password=postgresdb_settings.password,
                host=postgresdb_settings.host,
                port=postgresdb_settings.port,
                database=postgresdb_settings.database,
            )
        )
