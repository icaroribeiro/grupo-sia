# src/layers/data_access_layer/rest_api.py
from typing import Any
import requests
from src.client_error import ClientError
from src.layers.core_logic_layer.settings.app_settings import AppSettings


class RestAPIClient:
    def __init__(self, app_settings: AppSettings):
        self.base_url = app_settings.rest_api_url_path

    def get_healthcheck(self, url_path: str):
        url = f"{self.base_url}{url_path}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise ClientError(
                message="API health check failed",
                detail=f"An error occurred while health checking: {error}",
            )

    def upload_file(self, url_path: str, file_content: bytes) -> dict[str, Any]:
        url = f"{self.base_url}{url_path}"
        headers = {"Content-Type": "application/zip"}

        try:
            response = requests.post(url=url, data=file_content, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise ClientError(
                message="API file upload failed",
                detail=f"An error occurred while uploading: {error}",
            )
