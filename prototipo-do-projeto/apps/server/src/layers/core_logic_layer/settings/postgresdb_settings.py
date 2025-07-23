from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresDBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRESDB_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    driver: str = Field(default="postgresql+asyncpg")
    username: str = Field(default="postgresdbuser")
    password: str = Field(default="postgresdbpassword")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="notas_fiscais_db")
