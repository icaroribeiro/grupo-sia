from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StreamlitAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STREAMLIT_APP_",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_extra=True,
    )

    host: str = Field(default="localhost")
    port: int = Field(default=8501)
    data_input_upload_dir_path: str = Field(default="data/input/upload")
    data_output_workflow_dir_path: str = Field(default="data/output/workflow")
    data_output_upload_extracted_dir_path: str = Field(
        default="data/output/upload/extracted"
    )
    data_output_ingestion_dir_path: str = Field(default="data/output/ingestion")
    assets_dir_path: str = Field(default="assets")

    @staticmethod
    def get_year_list() -> List[int]:
        return [2025, 2024, 2023]

    @staticmethod
    def get_color_theme_list() -> List[str]:
        return ["Viridis", "Plasma", "Inferno", "Cividis"]

    @staticmethod
    def get_state_name_by_emitter_uf(uf_code: str) -> str:
        uf_map = {
            "AC": "Acre",
            "AL": "Alagoas",
            "AP": "Amapá",
            "AM": "Amazonas",
            "BA": "Bahia",
            "CE": "Ceará",
            "DF": "Distrito Federal",
            "ES": "Espírito Santo",
            "GO": "Goiás",
            "MA": "Maranhão",
            "MT": "Mato Grosso",
            "MS": "Mato Grosso do Sul",
            "MG": "Minas Gerais",
            "PA": "Pará",
            "PB": "Paraíba",
            "PR": "Paraná",
            "PE": "Pernambuco",
            "PI": "Piauí",
            "RJ": "Rio de Janeiro",
            "RN": "Rio Grande do Norte",
            "RS": "Rio Grande do Sul",
            "RO": "Rondônia",
            "RR": "Roraima",
            "SC": "Santa Catarina",
            "SP": "São Paulo",
            "SE": "Sergipe",
            "TO": "Tocantins",
        }

        cleaned_uf_code = uf_code.strip().upper() if isinstance(uf_code, str) else None

        return uf_map.get(cleaned_uf_code, f"Desconhecido ({uf_code})")
