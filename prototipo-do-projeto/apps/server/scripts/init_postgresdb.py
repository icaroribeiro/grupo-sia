import asyncio
import os

from sqlalchemy import text
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.postgresdb_settings import PostgresDBSettings
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


async def main() -> None:
    postgresdb_settings = PostgresDBSettings()
    postgresdb = PostgresDB(postgresdb_settings=postgresdb_settings)
    logger.info("Database startup initiating...")
    try:
        async with postgresdb.async_session() as async_session:
            sql_statement = text("""SELECT 1""")
            await async_session.execute(statement=sql_statement)
        message = "Success: Database connection is established."
        logger.info(message)
    except Exception as error:
        message = (
            f"Error: Failed to check if database connection is established: {error}"
        )
        logger.error(message)
        raise

    logger.info("Alembic migration run initiating...")
    try:
        os.system("alembic upgrade head")
        message = "Success: Alembic migration run complete."
        logger.info(message)
    except Exception as error:
        message = f"Error: Failed to run Alembic migration: {error}"
        logger.error(message)
        raise Exception(message)

    logger.info("Database closure initiating...")
    try:
        await postgresdb.close()
        message = "Success: Database closure complete."
        logger.info(message)
    except Exception as error:
        message = f"Error: Failed to close database: {error}"
        logger.error(message)
        raise Exception(message)


if __name__ == "__main__":
    asyncio.run(main())
