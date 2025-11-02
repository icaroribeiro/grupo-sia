import streamlit as st

from src.ai.models.invoice_ingestion_config_model import (
    InvoiceIngestionConfigModel,
)
from src.ai.models.invoice_item_ingestion_config_model import (
    InvoiceItemIngestionConfigModel,
)
from src.core.container.container import Container
from src.core.logging import logger
from src.infra.db.models.invoice_item_model import (
    InvoiceItemModel as SQLAlchemyInvoiceItemModel,
)
from src.infra.db.models.invoice_model import (
    InvoiceModel as SQLAlchemyInvoiceModel,
)
from src.streamlit_app import App

st.set_page_config(
    page_title="Gestão de NF-e com IA",
    layout="wide",
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
        container.wire(modules=["src.streamlit_app"])
        app: App = App()
        app.run()
        logger.info("Application execution completed.")
    except Exception as error:
        message = f"Failed to run application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    main()
