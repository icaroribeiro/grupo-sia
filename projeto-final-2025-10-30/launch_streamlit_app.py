import subprocess

from src.streamlit_app_layers.core_layer.logging import logger
from src.streamlit_app_layers.settings_layer.streamlit_app_settings import (
    StreamlitAppSettings,
)

if __name__ == "__main__":
    try:
        streamlit_app_settings = StreamlitAppSettings()
        logger.info("Streamlit application has started...")
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
        message = f"Failed to launch Streamlit application: {error}"
        logger.error(message)
