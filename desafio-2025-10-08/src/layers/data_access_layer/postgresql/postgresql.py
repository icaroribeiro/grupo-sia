import os
import asyncpg
from langchain_community.utilities.sql_database import SQLDatabase

from src.layers.core_logic_layer.settings.postgresql_settings import PostgreSQLSettings


class PostgreSQL(SQLDatabase):
    def __init__(self, postgresql_settings: PostgreSQLSettings):
        self.postgresql_settings = postgresql_settings

    def get_conn_string(self) -> str:
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            return database_url

        return (
            "{driver}://{user}:{password}@{host}:{port}/{db}?sslmode=disable"
        ).format(
            driver=self.postgresql_settings.driver,
            user=self.postgresql_settings.user,
            password=self.postgresql_settings.password,
            host=self.postgresql_settings.host,
            port=self.postgresql_settings.port,
            db=self.postgresql_settings.db,
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
