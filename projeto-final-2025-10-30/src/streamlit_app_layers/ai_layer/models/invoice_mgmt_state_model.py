from src.streamlit_app_layers.ai_layer.models.base_state_model import (
    BaseStateModel,
)


class InvoiceMgmtStateModel(BaseStateModel):
    ingestion_args_list: list[dict[str, str]] | None
    chart_data: dict | None = None
