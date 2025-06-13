from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    DATA_DIR: str = "data"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
