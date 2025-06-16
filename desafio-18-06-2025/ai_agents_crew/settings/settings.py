from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(default="your_gemini_api_key", env="GEMINI_API_KEY")
    DATA_DIR: str = Field(default="your_data_dir", env="DATA_DIR")

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
