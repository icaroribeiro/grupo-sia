from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    port: int = Field(default=8000)
    host: str = Field(default="localhost")
    output_data_dir_path: str = Field(default="data/output")
    import_data_dir_path: str = Field(default="data/import")
    upload_data_dir_path: str = Field(default="data/upload")
    upload_extracted_data_dir_path: str = Field(default="data/upload/extracted")
    ingestion_data_dir_path: str = Field(default="data/ingestion")
