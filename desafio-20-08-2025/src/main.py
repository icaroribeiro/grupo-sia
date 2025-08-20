import asyncio
from src.app import App
from src.layers.core_logic_layer.logging import logger


async def main():
    try:
        logger.info("Application startup has started...")
        app: App = App()
        await app.run()
        logger.info("Success: Application startup complete.")
    except Exception as error:
        message = f"Error: Failed to startup Application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    asyncio.run(main=main())
