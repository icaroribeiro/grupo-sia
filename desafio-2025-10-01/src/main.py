from src.streamlit_app import App
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger


def main() -> None:
    logger.info("Starting application execution...")
    try:
        container: Container = Container()
        container.wire(
            modules=[
                "src.streamlit_app",
                "src.layers.presentation_layer",
            ]
        )
        app: App = App()
        app.run()
        logger.info("Success: Application execution completed.")
    except Exception as error:
        message = f"Error: Failed to run application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    main()
