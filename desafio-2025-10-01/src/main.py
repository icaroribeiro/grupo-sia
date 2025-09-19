import asyncio
from src.app import App
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import ai_settings, app_settings


async def main() -> None:
    try:
        logger.info("Application startup has started...")
        app: App = App()
        container: Container = Container()
        container.config.ai_settings.from_value(ai_settings)
        container.config.app_settings.from_value(app_settings)
        container.wire(
            modules=[
                "src.app",
                "src.layers.presentation_layer",
            ]
        )
        await app.start()
        logger.info("Success: Application startup complete.")
    except Exception as error:
        message = f"Error: Failed to startup Application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    asyncio.run(main=main())
# import asyncio

# from src.app import App
# from src.layers.core_logic_layer.container.container import Container
# from src.layers.core_logic_layer.logging import logger

# from src.layers.core_logic_layer.settings import ai_settings, app_settings


# async def main() -> None:
#     try:
#         logger.info("Application startup has started...")
#         app: App = App()
#         container: Container = Container()
#         container.config.ai_settings.from_value(ai_settings)
#         container.config.app_settings.from_value(app_settings)
#         container.wire(
#             modules=[
#                 "src.app",
#                 "src.layers.presentation_layer",
#             ]
#         )
#         await app.start()
#         logger.info("Success: Application startup complete.")
#     except Exception as error:
#         message = f"Error: Failed to startup Application: {str(error)}"
#         logger.error(message)
#         raise


# if __name__ == "__main__":
#     asyncio.run(main=main())
