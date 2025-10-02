from src.layers.business_layer.ai_agents.models.base_state_model import BaseStateModel


class DataAnalysisStateModel(BaseStateModel):
    csv_file_paths: list[str] | None = None
    is_final_plot: dict[str, str | bool] | None = None
