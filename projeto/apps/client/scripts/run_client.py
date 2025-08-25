import os

from src.settings.settings import get_settings


def main() -> None:
    app_port = get_settings().port
    app_host = get_settings().host

    os.system(
        f"streamlit run src/main.py --server.port={app_port} --server.address={app_host}"
    )


if __name__ == "__main__":
    main()
