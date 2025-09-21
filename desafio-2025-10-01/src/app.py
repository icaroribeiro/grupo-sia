import uuid
import streamlit as st

from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.about_page import AboutPage
from src.layers.presentation_layer.chat_page import ChatPage
from src.layers.presentation_layer.home_page import HomePage
from src.layers.presentation_layer.plotting_page import PlottingPage
from src.layers.presentation_layer.upload_page import UploadPage
# from src.layers.presentation_layer.upload_page import UploadPage


class App:
    def __init__(self) -> None:
        st.sidebar.title("Navegação")
        if "session_thread_id" not in st.session_state:
            st.session_state.session_thread_id = str(uuid.uuid4())
            logger.info(
                f"New session started with thread_id: {st.session_state.session_thread_id}"
            )
        self.setup_pages()

    def setup_pages(self) -> None:
        self.__PAGES = {
            "home": {
                "title": "Ínicio",
                "func": HomePage().show,
            },
            "upload": {
                "title": "Upload",
                "func": UploadPage().show,
            },
            "chat": {
                "title": "Bate-Papo",
                "func": ChatPage().show,
            },
            "plotting": {
                "title": "Plotagem",
                "func": PlottingPage().show,
            },
            "about": {
                "title": "Sobre",
                "func": AboutPage().show,
            },
        }
        for page, value in self.__PAGES.items():
            st.sidebar.button(
                value["title"],
                on_click=self.__set_page,
                args=(page,),
                use_container_width=True,
            )
        self.current_page_name = st.query_params.get("page", "home")

    def run(self) -> None:
        page = self.__PAGES.get(self.current_page_name)
        if page["func"]:
            page["func"]()
        else:
            st.error("Page not found!")

    @staticmethod
    def __set_page(page_name: str) -> None:
        st.query_params["page"] = page_name
