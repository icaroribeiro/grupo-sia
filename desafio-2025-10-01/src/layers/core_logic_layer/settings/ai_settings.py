from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AI_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    llm_model: str = Field(default="gpt-4.1-nano")
    llm_temperature: float = Field(default=0.1)
    llm_api_key: str = Field(default=...)
