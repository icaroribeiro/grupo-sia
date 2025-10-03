from src.layers.business_layer.ai_agents.models.base_state_model import BaseStateModel


class DataIngestionStateModel(BaseStateModel):
    ingestion_args_list: list[dict[str, str]]
