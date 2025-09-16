# src/layers/presentation_layer/home_page.py
import streamlit as st
from src.layers.core_logic_layer.settings.app_settings import AppSettings
from src.layers.data_access_layer.rest_api.rest_api_client import RestAPIClient
from src.client_error import ClientError


class HomePage:
    __URL_PATH = "/healthcheck"

    def __init__(self, app_settings: AppSettings):
        self.rest_api_client = RestAPIClient(app_settings=app_settings)

    def show(self):
        st.title("🏡 Home Page")
        st.write("Welcome to the homepage!")
        st.write("This is where you can find general information about our app.")

        st.header("API Status")

        if st.button("Check API Status"):
            with st.spinner("Pinging API..."):
                try:
                    response = self.rest_api_client.get_healthcheck(
                        url_path=self.__URL_PATH,
                    )
                    if response:
                        st.success("API is healthy! ✅")
                        st.json(response)
                    else:
                        st.error(
                            "API is not responding or returned an empty response. ❌"
                        )
                except ClientError as e:
                    st.error(f"API is not healthy. Error: {e.error_details.message}")
                    if e.error_details.detail:
                        st.info(e.error_details.detail)
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
