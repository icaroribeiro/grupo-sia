from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = Field(default=8501)
    host: str = Field(default="localhost")

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_ignore_extra=True,
    )


def get_settings() -> Settings:
    return Settings()
