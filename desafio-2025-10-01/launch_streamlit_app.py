import subprocess

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)

if __name__ == "__main__":
    try:
        streamlit_app_settings = StreamlitAppSettings()
        subprocess.run(
            [
                "streamlit",
                "run",
                "src/main.py",
                "--server.address",
                f"{streamlit_app_settings.host}",
                "--server.port",
                f"{streamlit_app_settings.port}",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        message = "Streamlit application closed due to KeyboardInterrupt"
        logger.error(message)
    except Exception as error:
        message = f"Error: Failed to initiate Streamlit application: {error}"
        logger.error(message)
