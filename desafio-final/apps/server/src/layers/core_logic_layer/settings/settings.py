from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = Field(default=8000)
    host: str = Field(default="localhost")
    llm: str = Field(default="gemini")
    openai_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    zip_path: str = Field(default="zip_path")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_ignore_extra=True,
    )


def get_settings() -> Settings:
    return Settings()
