import os
import streamlit as st

from dependency_injector.wiring import Provide, inject

from src.layers.business_layer.ai_agents.workflows.credit_card_fraud_analysis_workflow import (
    CreditCardFraudAnalysisWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.settings.app_settings import AppSettings
from src.layers.core_logic_layer.logging import logger


class HomePage:
    def __init__(self) -> None:
        if "file_uploaded" not in st.session_state:
            st.session_state.file_uploaded = ""
        if "process_workflow" not in st.session_state:
            st.session_state.process_workflow = False

    async def show(self) -> None:
        st.title("🏡 Home Page")
        st.write("Welcome to the homepage!")
        st.write("This is where you can find general information about our app.")
        print(f"1 - {st.session_state.process_workflow}")
        # Display file upload widget only if no file is uploaded
        if not st.session_state.file_uploaded:
            self.handle_file_upload()
        else:
            st.info(f"📁 Arquivo .zip carregado: {st.session_state.file_uploaded}")
            if st.button("📄 Enviar novo arquivo .zip"):
                st.session_state.file_uploaded = ""
                st.session_state.process_workflow = False
                st.rerun()

        # Separately handle workflow execution
        print(f"2 - {st.session_state.process_workflow}")
        if st.session_state.process_workflow:
            await self.run_workflow()
            # Reset the flag after the workflow has run to prevent repetition
            st.session_state.process_workflow = False
            st.rerun()

    @inject
    def handle_file_upload(
        self,
        app_settings: AppSettings = Provide[Container.config.app_settings],
    ):
        file = st.file_uploader("📤 Envie um arquivo .zip", type=["zip"])
        if file is not None:
            try:
                upload_data_dir_path = app_settings.upload_data_dir_path
                self.__delete_non_hidden_files(dir_path=upload_data_dir_path)

                upload_extracted_data_dir_path = (
                    app_settings.upload_extracted_data_dir_path
                )
                self.__delete_non_hidden_files(dir_path=upload_extracted_data_dir_path)

                file_path = os.path.join(upload_data_dir_path, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                st.success(f"Arquivo .zip submetido com sucesso!: {file.name}")

                st.session_state.file_uploaded = file_path
                # Set flag to run the workflow on the next rerun
                st.session_state.process_workflow = True
                st.rerun()  # Trigger a rerun to execute the workflow block

            except Exception as error:
                message = f"Error: Failed to save ZIP archive: {error}"
                logger.error(message)
                st.error(message)

    @inject
    async def run_workflow(
        self,
        app_settings: AppSettings = Provide[Container.config.app_settings],
        credit_card_fraud_analysis_workflow: CreditCardFraudAnalysisWorkflow = Provide[
            Container.credit_card_fraud_analysis_workflow
        ],
    ):
        file_path = st.session_state.file_uploaded
        upload_extracted_data_dir_path = app_settings.upload_extracted_data_dir_path

        with st.spinner("Executing fraud analysis workflow..."):
            try:
                prompt = f"""
                INSTRUCTIONS:
                - Perform a multi-step procedure to unzip a ZIP archive.
                - The procedure consists of the following tasks directed to credit card fraud analysis team:
                    1. Unzip files from ZIP archive located at '{file_path}' to the directory '{upload_extracted_data_dir_path}'.
                CRITICAL RULES:
                - DO NOT proceed with one task if the previous only was not completed.
                - DO NOT perform handoffs in parallel.
                """

                result = await credit_card_fraud_analysis_workflow.run(
                    input_message=prompt
                )
                logger.info("Workflow executed!")
                st.success("Workflow completed successfully!")

            except Exception as error:
                message = f"Error: Failed to run fraud analysis workflow: {error}"
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
                    print(f"Deleted: {file_name}")
        except Exception as error:
            message = f"Error: Failed to delete files in directory: {error}"
            logger.error(message)
            st.error(message)
