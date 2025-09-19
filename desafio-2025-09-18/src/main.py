import asyncio
from src.app import App
from src.layers.core_logic_layer.logging import logger


async def main() -> None:
    logger.info("Starting application execution...")
    try:
        app: App = App()
        await app.run()
        logger.info("Success: Application execution completed.")
    except Exception as error:
        message = f"Error: Failed to run application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    asyncio.run(main=main())
