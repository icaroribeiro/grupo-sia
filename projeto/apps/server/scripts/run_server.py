import subprocess

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import app_settings

if __name__ == "__main__":
    try:
        subprocess.run(
            [
                "uvicorn",
                "src.main:app",
                "--host",
                f"{app_settings.host}",
                "--port",
                f"{app_settings.port}",
                "--reload",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        message = "Uvicorn server closed due to KeyboardInterrupt"
        logger.error(message)
    except subprocess.CalledProcessError as error:
        message = f"Error: Uvicorn server exited with an error: {error}"
        logger.error(message)
    except Exception as error:
        message = f"Error: Failed to initiate Uvicorn server: {error}"
        logger.error(message)
