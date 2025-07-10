from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    llm_provider: str = Field(default="gemini")
    llm_model: str = Field(default="gemini/gemini-2.0-flash")
    llm_api_key: str = Field(default=...)
    llm_temperature: float = Field(default=0.1)

    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_ignore_extra=True,
    )
