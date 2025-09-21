from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRES_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    driver: str = Field(default="postgresql")
    db: str = Field(default="langchain_chat_history")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
