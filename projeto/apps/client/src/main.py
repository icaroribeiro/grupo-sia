from src.client import Client

from src.layers.core_logic_layer.logging import logger


try:
    logger.info("Client startup has started...")
    client: Client = Client()
    logger.info("Success: Client startup complete.")
except Exception as error:
    message = f"Error: Failed to startup Client: {str(error)}"
    logger.error(message)
    raise


if __name__ == "__main__":
    pass
