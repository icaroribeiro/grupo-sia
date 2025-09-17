import streamlit as st

from src.layers.presentation_layer.home_page import HomePage


class App:
    def __init__(self) -> None:
        st.sidebar.title("Navigation")
        self.setup_pages()

    def setup_pages(self) -> None:
        self.__PAGES = {
            "Home": HomePage().show,
        }
        for page_name in self.__PAGES.keys():
            st.sidebar.button(
                page_name,
                on_click=self.__set_page,
                args=(page_name,),
                use_container_width=True,
            )
        self.current_page_name = st.query_params.get("page", "Home")

    async def start(self):
        page_func = self.__PAGES.get(self.current_page_name)
        if page_func:
            await page_func()
        else:
            st.error("Page not found!")

    @staticmethod
    def __set_page(page_name: str) -> None:
        st.query_params["page"] = page_name
