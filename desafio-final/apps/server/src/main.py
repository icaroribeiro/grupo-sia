import uvicorn

from src.layers.core_logic_layer.settings.settings import Settings


if __name__ == "__main__":
    uvicorn.run(
        app="src:app",
        host="0.0.0.0",
        port=int(Settings().port),
    )
