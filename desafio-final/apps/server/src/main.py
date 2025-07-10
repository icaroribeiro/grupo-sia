import uvicorn
from fastapi import FastAPI

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.settings import Settings
from src.server import Server

app: FastAPI | None = None

try:
    logger.info("Server startup initiating...")
    server: Server = Server()
    app = server.get_app()
    logger.info("Server startup complete.")
except Exception as error:
    message = f"Got an error when starting up the server: {str(error)}"
    logger.error(message)
    raise


if __name__ == "__main__":
    try:
        if app is not None:
            uvicorn.run(
                app=app,
                host="0.0.0.0",
                port=int(Settings().port),
            )
        else:
            message = (
                "Got an error when initiating the application: application is None"
            )
            logger.info(message)
    except Exception as error:
        message = f"Got and error when starting the uvicorn server: {error}"
        logger.error(message)
