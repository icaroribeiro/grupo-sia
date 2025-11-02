import asyncio
import os

from sqlalchemy import text

from src.core.logging import logger
from src.infra.db.postgresql import PostgreSQL
from src.settings.postgresql_db_settings import (
    PostgreSQLDBSettings,
)


async def main() -> None:
    postgresql_db_settings = PostgreSQLDBSettings()
    postgresql = PostgreSQL(postgresql_db_settings=postgresql_db_settings)
    logger.info("Postgres database migration has started...")

    logger.info("Database connection checking has started...")
    try:
        async with postgresql.async_session() as async_session:
            sql_statement = text("""SELECT 1""")
            await async_session.execute(statement=sql_statement)
        logger.info("Database connection is established.")
    except Exception as error:
        message = f"Failed to establish database connection: {error}"
        logger.error(message)
        raise

    logger.info("Alembic migration has started...")
    try:
        os.system("alembic upgrade head")
        logger.info("Alembic migration complete.")
    except Exception as error:
        message = f"Failed to migrate Alembic: {error}"
        logger.error(message)

    logger.info("Database connection closure has started...")
    try:
        await postgresql.close()
        logger.info("Database connection is closed.")
    except Exception as error:
        message = f"Failed to close database connection: {error}"
        logger.error(message)


if __name__ == "__main__":
    asyncio.run(main())
