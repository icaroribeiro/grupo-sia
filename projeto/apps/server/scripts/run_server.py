import subprocess

from src.layers.core_logic_layer.logging import logger


def main() -> None:
    try:
        subprocess.run(["uv", "run", "src/main.py"], check=True)
    except KeyboardInterrupt:
        message = "Uvicorn server closed due to KeyboardInterrupt"
        logger.error(message)
    except subprocess.CalledProcessError as error:
        message = f"Error: Uvicorn server exited with an error: {error}"
        logger.error(message)
    except Exception as error:
        message = f"Error: Failed to initiate Uvicorn server: {error}"
        logger.error(message)


if __name__ == "__main__":
    main()
