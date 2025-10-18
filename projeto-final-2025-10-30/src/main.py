import streamlit as st
from src.layers.business_layer.ai_agents.models.invoice_ingestion_config_model import (
    InvoiceIngestionConfigModel,
)
from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_config_model import (
    InvoiceItemIngestionConfigModel,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.streamlit_app import App
from src.layers.data_access_layer.db.postgresql.models.invoice_model import (
    InvoiceModel as SQLAlchemyInvoiceModel,
)
from src.layers.data_access_layer.db.postgresql.models.invoice_item_model import (
    InvoiceItemModel as SQLAlchemyInvoiceItemModel,
)

st.set_page_config(
    # page_title="Dashboard de NF-e", # You can set a custom title
    # page_icon="🇧🇷", # Use a relevant icon
    layout="wide",  # This is the crucial setting
    initial_sidebar_state="expanded",
)


def main() -> None:
    logger.info("Starting application execution...")
    try:
        container: Container = Container()
        container.config.ingestion_config_dict.from_value(
            {
                0: InvoiceIngestionConfigModel().model_dump(),
                1: InvoiceItemIngestionConfigModel().model_dump(),
            }
        )
        container.config.sqlalchemy_model_by_table_name.from_value(
            {
                SQLAlchemyInvoiceModel.get_table_name(): SQLAlchemyInvoiceModel,
                SQLAlchemyInvoiceItemModel.get_table_name(): SQLAlchemyInvoiceItemModel,
            }
        )
        container.wire(
            modules=[
                "src.streamlit_app",
                "src.layers.presentation_layer",
            ]
        )
        app: App = App()
        app.run()
        logger.info("Application execution completed.")
    except Exception as error:
        message = f"Failed to run application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    main()
