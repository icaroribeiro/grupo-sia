import uvicorn
from fastapi import FastAPI

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import app_settings
from src.server import Server

app: FastAPI | None = None

try:
    logger.info("Server startup has started...")
    server: Server = Server()
    app = server.app
    logger.info("Success: Server startup complete.")
except Exception as error:
    message = f"Error: Failed to startup Server: {str(error)}"
    logger.error(message)
    raise


if __name__ == "__main__":
    if app is not None:
        try:
            logger.info("Uvicorn server startup has started...")
            uvicorn.run(
                app="main:app", host="0.0.0.0", port=int(app_settings.port), reload=True
            )
        except Exception as error:
            message = f"Error: Failed to startup Uvicorn server: {error}"
            logger.error(message)
            raise Exception(message)
    else:
        message = "Error: Server hasn't initialized FastAPI application."
        logger.info(message)
        raise Exception(message)
