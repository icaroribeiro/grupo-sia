from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = Field(default=8000)
    host: str = Field(default="localhost")
    imports_data_dir_path: str = Field(default="data/imports")
    uploads_data_dir_path: str = Field(default="data/uploads")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_ignore_extra=True,
    )


def get_settings() -> Settings:
    return Settings()
