import asyncio
import os

from sqlalchemy import text
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.postgresdb_settings import PostgresDBSettings
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


async def main() -> None:
    logger.info("Postgres database migration has started...")
    postgresdb_settings = PostgresDBSettings()
    postgresdb = PostgresDB(postgresdb_settings=postgresdb_settings)
    logger.info("Database connection establishment has started...")
    try:
        async with postgresdb.async_session() as async_session:
            sql_statement = text("""SELECT 1""")
            await async_session.execute(statement=sql_statement)
        message = "Success: Database connection is established."
        logger.info(message)
    except Exception as error:
        message = f"Error: Failed to establish database connection: {error}"
        logger.error(message)
        raise

    logger.info("Alembic migration run has started...")
    try:
        os.system("alembic upgrade head")
        message = "Success: Alembic migration run complete."
        logger.info(message)
    except Exception as error:
        message = f"Error: Failed to run Alembic migration: {error}"
        logger.error(message)
        raise Exception(message)

    logger.info("Database connection closure has started...")
    try:
        await postgresdb.close()
        message = "Success: Database connection closure complete."
        logger.info(message)
    except Exception as error:
        message = f"Error: Failed to close database connection: {error}"
        logger.error(message)
        raise Exception(message)


if __name__ == "__main__":
    asyncio.run(main())
