import subprocess

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import app_settings

if __name__ == "__main__":
    try:
        subprocess.run(
            [
                "streamlit",
                "run",
                "src/main.py",
                "--server.address",
                f"{app_settings.host}",
                "--server.port",
                f"{app_settings.port}",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        message = "Streamlit client closed due to KeyboardInterrupt"
        logger.error(message)
    except Exception as error:
        message = f"Error: Failed to initiate Streamlit client: {error}"
        logger.error(message)
