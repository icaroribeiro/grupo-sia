import uuid

import streamlit as st

from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.about_page import AboutPage
from src.layers.presentation_layer.ead_page import EADPage
from src.layers.presentation_layer.home_page import HomePage
from src.layers.presentation_layer.test_page import TestPage


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
            "ead": {
                "title": "A.E.D.",
                "func": EADPage().show,
            },
            "about": {
                "title": "Sobre",
                "func": AboutPage().show,
            },
            "test": {
                "title": "Test",
                "func": TestPage().show,
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
