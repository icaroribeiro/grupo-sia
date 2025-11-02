from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgreSQLDBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRESQL_DB_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    driver: str = Field(default="postgresql")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    db: str = Field(default="invoices_db")
