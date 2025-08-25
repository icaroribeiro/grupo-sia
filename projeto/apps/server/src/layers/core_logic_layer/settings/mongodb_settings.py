from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MONGODB_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    driver: str = Field(default="mongodb")
    username: str = Field(default="mongodbuser")
    password: str = Field(default="mongodbpassword")
    host: str = Field(default="localhost")
    port: int = Field(default=27017)
    database: str = Field(default="notas_fiscais_db")
    cache_expiration_time_in_seconds: int = Field(default=60)
    cache_capacity: int = Field(default=1000)
