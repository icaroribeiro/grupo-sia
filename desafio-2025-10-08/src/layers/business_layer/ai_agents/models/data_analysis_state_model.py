from src.layers.business_layer.ai_agents.models.base_state_model import BaseStateModel


class DataAnalysisStateModel(BaseStateModel):
    csv_file_paths: list[str] | None = None
    final_chart_data: dict | None = None
