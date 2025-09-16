# src/client.py
import streamlit as st

# Import your page functions
from src.layers.core_logic_layer.settings import app_settings
from src.layers.presentation_layer.home_page import HomePage
from src.layers.presentation_layer.about_page import show as show_about_page
from src.layers.presentation_layer.data_ingestion_page import DataIngestionPage

# A dictionary to map page names to their corresponding functions


# Define a callback function to set the page in query params


class Client:
    __PAGES = {
        "Home": HomePage(app_settings=app_settings).show,
        "About": show_about_page,
        "Data Ingestion": DataIngestionPage(app_settings=app_settings).show,
    }

    def __init__(self) -> None:
        st.sidebar.title("Navigation")

        # Create buttons with a callback to set the page
        for page_name in self.__PAGES.keys():
            st.sidebar.button(
                page_name,
                on_click=self.__set_page,
                args=(page_name,),
                use_container_width=True,
            )

        # Get the current page from the URL query parameters
        current_page_name = st.query_params.get("page", "Home")

        # Display the selected page content based on the URL
        page_func = self.__PAGES.get(current_page_name)
        if page_func:
            page_func()
        else:
            st.error("Page not found!")

    @staticmethod
    def __set_page(page_name: str) -> None:
        st.query_params["page"] = page_name
