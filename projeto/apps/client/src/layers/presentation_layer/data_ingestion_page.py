# src/layers/presentation_layer/data_ingestion_page.py
import streamlit as st
from src.layers.core_logic_layer.settings.app_settings import AppSettings
from src.layers.data_access_layer.rest_api.rest_api_client import RestAPIClient
from src.client_error import ClientError


class DataIngestionPage:
    __URL_PATH = "/data-ingestion"

    def __init__(self, app_settings: AppSettings):
        self.rest_api_client = RestAPIClient(app_settings=app_settings)

    def show(self):
        st.title("📂 Data Ingestion Page")
        st.write("This page is for uploading and managing data.")

        uploaded_file = st.file_uploader("Choose a file to upload", type=["zip"])

        if uploaded_file is not None:
            if st.button("Upload File to API"):
                st.info("Uploading file... Please wait.")
                try:
                    file_content = uploaded_file.getvalue()
                    file_name = uploaded_file.name

                    response_data = self.rest_api_client.upload_file(
                        url_path=self.__URL_PATH,
                        file_content=file_content,
                        file_name=file_name,
                    )

                    if response_data:
                        st.success("File uploaded successfully!")
                        st.json(response_data)
                except ClientError as e:
                    st.error(f"Error: {e.error_details.message}")
                    if e.error_details.detail:
                        st.info(e.error_details.detail)
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
