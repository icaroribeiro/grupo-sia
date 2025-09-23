import os
import uuid
import streamlit as st
import asyncio
from dependency_injector.wiring import Provide, inject
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.core_logic_layer.logging import logger


class UploadPage:
    @inject
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings = Provide[
            Container.streamlit_app_settings
        ],
        data_analysis_workflow=Provide[Container.data_analysis_workflow],
        workflow_runner: WorkflowRunner = Provide[Container.workflow_runner],
    ) -> None:
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = str(uuid.uuid4())
        if "data_ready_for_chat" not in st.session_state:
            st.session_state.data_ready_for_chat = False
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = ""
        self.streamlit_app_settings = streamlit_app_settings
        self.data_analysis_workflow = data_analysis_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("📤 Upload de Arquivo `.zip`")
        st.write("Carregue um arquivo `.zip` para iniciar a análise de dados.")

        if not st.session_state.uploaded_file:
            self.upload_file()
        else:
            st.info(f"📁 Arquivo `.zip` carregado: {st.session_state.uploaded_file}")
            if st.button("📄 Carregar novo arquivo `.zip`"):
                st.session_state.uploaded_file = ""
                st.session_state.data_ready_for_chat = False
                st.rerun()

        if st.session_state.uploaded_file and not st.session_state.data_ready_for_chat:
            self.decompress_file()

    def upload_file(
        self,
    ):
        zip_file = st.file_uploader("📤 Carregar um arquivo .zip", type=["zip"])
        if zip_file is not None:
            try:
                upload_data_dir_path = self.streamlit_app_settings.upload_data_dir_path
                self.__delete_non_hidden_files(dir_path=upload_data_dir_path)
                upload_extracted_data_dir_path = (
                    self.streamlit_app_settings.upload_extracted_data_dir_path
                )
                self.__delete_non_hidden_files(dir_path=upload_extracted_data_dir_path)
                file_path = os.path.join(upload_data_dir_path, zip_file.name)
                with open(file_path, "wb") as f:
                    f.write(zip_file.getbuffer())
                st.success(f"Successfully submitted .zip file!: {zip_file.name}")
                st.session_state.uploaded_file = file_path
                st.rerun()
            except Exception as error:
                message = f"Error: Failed to save ZIP archive: {error}"
                logger.error(message)
                st.error(message)

    def decompress_file(
        self,
    ):
        file_path = st.session_state.uploaded_file
        upload_extracted_data_dir_path = (
            self.streamlit_app_settings.upload_extracted_data_dir_path
        )

        with st.spinner("Starting workflow to decompress the file..."):
            try:
                input_message = f"""
                INSTRUCTIONS:
                    - Perform the following tasks:
                        1. Unzip files from ZIP archive located at '{file_path}' to the directory '{upload_extracted_data_dir_path}'.
                CRITICAL RULES:
                    - DO NOT call handoffs in parallel. Always assign work to one agent if the previous was completed.
                """
                asyncio.run(
                    self.workflow_runner.run_workflow(
                        self.data_analysis_workflow.workflow,
                        input_message,
                        st.session_state.session_thread_id,
                    )
                )
                st.session_state.data_ready_for_chat = True
                st.success("✅ File decompressed and data is ready for analysis!")
                st.rerun()
            except Exception as error:
                message = f"Error: Failed to run  data analysis workflow: {error}"
                logger.error(message)
                st.error(message)

    @staticmethod
    def __delete_non_hidden_files(dir_path: str) -> None:
        try:
            for file_name in os.listdir(dir_path):
                if not file_name.startswith(".") and os.path.isfile(
                    os.path.join(dir_path, file_name)
                ):
                    os.remove(os.path.join(dir_path, file_name))
        except Exception as error:
            message = f"Error: Failed to delete non hidden files in directory: {error}"
            logger.error(message)
            st.error(message)
