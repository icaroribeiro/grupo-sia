from src.layers.core_logic_layer.logging import logger
from src.server import Server


try:
    server = Server()
    app = server.get_app()
except Exception as error:
    message = f"Got an error when starting up server: {str(error)}"
    logger.error(message)
    raise
