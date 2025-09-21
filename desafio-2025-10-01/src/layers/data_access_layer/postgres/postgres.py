# src\layers\data_access_layer\postgres\postgres.py
import asyncpg
from langchain_community.utilities.sql_database import SQLDatabase

from src.layers.core_logic_layer.settings.postgres_settings import PostgresSettings


class Postgres(SQLDatabase):
    def __init__(self, postgres_settings: PostgresSettings):
        self.postgres_settings = postgres_settings

    def get_conn_string(self) -> str:
        return (
            "{driver}://{user}:{password}@{host}:{port}/{db}?sslmode=disable"
        ).format(
            driver=self.postgres_settings.driver,
            user=self.postgres_settings.user,
            password=self.postgres_settings.password,
            host=self.postgres_settings.host,
            port=self.postgres_settings.port,
            db=self.postgres_settings.db,
        )

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
