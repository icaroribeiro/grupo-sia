from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    port: int = Field(default=5000)
    host: str = Field(default="localhost")
    rest_api_url_path: str = Field(default="http://localhost:8000/api/v1")
