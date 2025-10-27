import uuid

import streamlit as st


from src.streamlit_app_layers.core_layer.logging import logger
from src.streamlit_app_layers.presentation_layer.pages.about_page import AboutPage
from src.streamlit_app_layers.presentation_layer.pages.chat_page import ChatPage
from src.streamlit_app_layers.presentation_layer.pages.data_analysis_page import (
    DataAnalysisPage,
)
from src.streamlit_app_layers.presentation_layer.pages.data_modeling_page import (
    DataModelingPage,
)
from src.streamlit_app_layers.presentation_layer.pages.invoice_ingestion_page import (
    InvoiceIngestionPage,
)

from src.streamlit_app_layers.presentation_layer.pages.home_page import HomePage


class App:
    def __init__(self) -> None:
        st.sidebar.title("Navegação")
        if "session_thread_id" not in st.session_state:
            st.session_state.session_thread_id = str(uuid.uuid4())
            logger.info(
                f"New session started with thread_id: {st.session_state.session_thread_id}"
            )
        self.__setup_pages()

    def __setup_pages(self) -> None:
        self.__pages = {
            "home": {
                "title": "Ínicio",
                "func": HomePage().show,
            },
            "data_modeling": {
                "title": "Modelagem de Dados",
                "func": DataModelingPage().show,
            },
            "invoice_ingestion": {
                "title": "Ingestão de NF-e",
                "func": InvoiceIngestionPage().show,
            },
            "data_analysis": {
                "title": "Análise de Dados",
                "func": DataAnalysisPage().show,
            },
            "chat": {
                "title": "Bate-Papo",
                "func": ChatPage().show,
            },
            "about": {
                "title": "Sobre",
                "func": AboutPage().show,
            },
        }
        for page, value in self.__pages.items():
            st.sidebar.button(
                value["title"],
                on_click=self.__set_page,
                args=(page,),
                use_container_width=True,
            )
        self.current_page_name = st.query_params.get("page", "home")

    def run(self) -> None:
        page = self.__pages.get(self.current_page_name)
        func = page.get("func", None)
        if func:
            func()
        else:
            logger.error("Page function not found!")
            st.error("Page function not found!")

    @staticmethod
    def __set_page(page_name: str) -> None:
        st.query_params["page"] = page_name
