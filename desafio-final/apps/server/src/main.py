import uvicorn
from fastapi import FastAPI

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import app_settings
from src.server import Server

app: FastAPI | None = None

try:
    logger.info("Started initiating Server...")
    server: Server = Server()
    app = server.app
    logger.info("Success: Server initiated.")
except Exception as error:
    message = f"Error: Failed to initiate Server: {str(error)}"
    logger.error(message)
    raise


if __name__ == "__main__":
    if app is not None:
        try:
            logger.info("Started initiating Uvicorn server...")
            uvicorn.run(
                app=app,
                host="0.0.0.0",
                port=int(app_settings.port),
            )
            message = "Success: Uvicorn server initiated."
            logger.info(message)
        except Exception as error:
            message = f"Error: Failed to start Uvicorn server: {error}"
            logger.error(message)
            raise Exception(message)
    else:
        message = "Error: Failed to initiate application: application is None"
        logger.info(message)
        raise Exception(message)
