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

    llm_provider: str = Field(default="google_genai")
    llm_model: str = Field(default="gemini-2.0-flash")
    llm_temperature: float = Field(default=0.1)
    llm_api_key: str = Field(default=...)
