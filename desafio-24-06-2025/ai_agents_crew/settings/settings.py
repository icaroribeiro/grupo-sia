from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM: str = Field(default=..., env="LLM")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    DATA_DIR: str = Field(default=..., env="DATA_DIR")

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
