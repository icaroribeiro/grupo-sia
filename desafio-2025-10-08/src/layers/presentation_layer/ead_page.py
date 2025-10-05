import asyncio
import json
import os
import re
from typing import Any

import pandas as pd
import streamlit as st
from dependency_injector.wiring import Provide, inject

from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)


class EADPage:
    @inject
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings = Provide[
            Container.streamlit_app_settings
        ],
        data_analysis_workflow: DataAnalysisWorkflow = Provide[
            Container.data_analysis_workflow
        ],
        workflow_runner: WorkflowRunner = Provide[Container.workflow_runner],
    ) -> None:
        if "aed_chat_history" not in st.session_state:
            st.session_state.aed_chat_history = []
        if "data_ready_for_chat" not in st.session_state:
            st.session_state.data_ready_for_chat = False
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = ""
        if "extracted_csv_path" not in st.session_state:
            st.session_state.extracted_csv_path = None

        self.streamlit_app_settings = streamlit_app_settings
        self.data_analysis_workflow = data_analysis_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("💡 Análise Exploratória de Dados")
        if st.session_state.data_ready_for_chat and st.session_state.extracted_csv_path:
            self.__display_data_sample()
        with st.sidebar:
            st.header("Upload de Arquivo 📥")
            if not st.session_state.uploaded_file:
                self.upload_file()
            else:
                st.info(
                    f"📁 Arquivo carregado: {os.path.basename(st.session_state.uploaded_file)}"
                )
                if st.button("🔄 Iniciar Nova Análise/Fazer Upload"):
                    st.session_state.uploaded_file = ""
                    st.session_state.data_ready_for_chat = False
                    st.session_state.aed_chat_history = []
                    st.session_state.extracted_csv_path = None
                    st.rerun()

        if st.session_state.uploaded_file and not st.session_state.data_ready_for_chat:
            self.decompress_file()
            return

        chat_container = st.container()
        with chat_container:
            if not st.session_state.uploaded_file:
                st.info(
                    "Por favor, carregue um arquivo .zip na barra lateral para começar a análise."
                )
            elif not st.session_state.data_ready_for_chat:
                st.warning("Arquivo carregado! Processando dados...")
            else:
                for message in st.session_state.aed_chat_history:
                    with st.chat_message("user"):
                        st.markdown(message["question"])
                    with st.chat_message("assistant"):
                        response_data = self.__extract_json_from_content(
                            message["answer"]
                        )
                        self._display_assistant_response(response_data)
        prompt = st.chat_input(
            "Escreva sua pergunta ou solicite um gráfico...",
            disabled=not st.session_state.data_ready_for_chat,
        )

        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            self.process_aed_question(question=prompt)

    def __display_data_sample(self):
        csv_path = st.session_state.extracted_csv_path
        if not csv_path or not os.path.exists(path=csv_path):
            logger.error("Caminho do arquivo CSV extraído não encontrado.")
            return
        try:
            dataframe = pd.read_csv(filepath_or_buffer=csv_path)
            with st.expander(
                f"👁️ Amostra dos Dados Carregados ({os.path.basename(csv_path)})"
            ):
                st.write(
                    f"Primeiras **{len(dataframe.head())} linhas** de **{len(dataframe)} registros**:"
                )
                st.dataframe(dataframe.head())
                st.subheader("Tipos de Colunas:")
                dtype_df = dataframe.dtypes.rename("Tipo").to_frame()
                dtype_df["Tipo"] = dtype_df["Tipo"].astype(str)
                st.dataframe(dtype_df)
        except Exception as error:
            st.error(f"Erro ao ler ou exibir a amostra do arquivo CSV: {error}")
            logger.error(f"Erro ao ler CSV em {csv_path}: {error}")

    def upload_file(self):
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
                message = f"Failed to save ZIP archive: {error}"
                logger.error(message)
                st.error(message)

    def decompress_file(self):
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
                response = asyncio.run(
                    self.workflow_runner.run_workflow(
                        self.data_analysis_workflow,
                        input_message,
                        st.session_state.session_thread_id,
                    )
                )
                final_message = response["messages"][-1]
                logger.info(f"final_message: {final_message}\n\n")
                final_response_str = final_message.content
                logger.info(f"final_response_str: {final_response_str}\n\n")
                extracted_files = [
                    os.path.join(upload_extracted_data_dir_path, f)
                    for f in os.listdir(upload_extracted_data_dir_path)
                    if f.endswith(".csv")
                ]
                if not extracted_files:
                    raise FileNotFoundError(
                        "Nenhum arquivo CSV encontrado após a descompressão. Certifique-se de que o ZIP contém um CSV."
                    )
                st.session_state.extracted_csv_path = extracted_files[0]
                st.session_state.data_ready_for_chat = True
                st.success(
                    "✅ Arquivo descompactado e os dados estão prontos para análise!"
                )
                st.rerun()

            except Exception as error:
                message = f"Failed to run data analysis workflow or locate CSV: {error}"
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
            message = f"Failed to delete non hidden files in directory: {error}"
            logger.error(message)
            st.error(message)

    def _display_assistant_response(self, response_data: Any) -> None:
        try:
            # logger.info(
            #     f"Response data for display: {json.dumps(response_data, indent=2)}"
            # )
            if isinstance(response_data, dict):
                if "chart" in response_data:
                    chart_raw = response_data.get("chart")
                    chart = self.__unescape_dict(chart_raw)
                    st.vega_lite_chart(chart, use_container_width=True)
                if "description" in response_data:
                    description_raw = response_data.get(
                        "description", "Gráfico gerado."
                    )
                    description = description_raw.encode().decode("unicode_escape")
                    st.markdown(f"**Análise Concluída:** {description}")
                if "error" in response_data:
                    st.error(response_data["error"])
            else:
                st.markdown(response_data)
        except (json.JSONDecodeError, TypeError) as error:
            logger.info(
                f"Non-JSON response (expected text summary). Displaying as markdown. Error details: {error}"
            )
            st.markdown(response_data)

    def process_aed_question(self, question: str) -> None:
        try:
            with st.spinner("💡 Gerando resposta ou gráfico..."):
                input_message = f"""
                    A user has submitted the following query from the chat interface: "{question}"
                    Your primary task is to analyze this query and route it to the most appropriate specialist agent (either the Unzip File Agent or the Data Analysis Agent) based on your internal instructions.
                    Formulate a clear and precise handoff task for the chosen specialist agent to execute.
                """
                response = asyncio.run(
                    self.workflow_runner.run_workflow(
                        self.data_analysis_workflow,
                        input_message,
                        st.session_state.session_thread_id,
                    )
                )
                final_message = response["messages"][-1]
                logger.info(f"final_message: {final_message}\n\n")
                final_response_str = final_message.content
                logger.info(f"final_response_str: {final_response_str}\n\n")
                tool_calls = final_message.additional_kwargs.get("tool_calls", [])
                response_data = self.__extract_json_from_content(final_response_str)
                with st.chat_message("assistant"):
                    self._display_assistant_response(response_data)
                    if tool_calls:
                        st.json(tool_calls)
                st.session_state.aed_chat_history.append(
                    {"question": question, "answer": final_response_str}
                )
        except Exception as error:
            logger.error(
                f"An UNEXPECTED error occurred when processing query: {error}",
                exc_info=True,
            )
            final_response = "⚠️ Ocorreu um erro catastrófico ao processar sua pergunta."
            with st.chat_message("assistant"):
                st.error(final_response)
            st.session_state.aed_chat_history.append(
                {"question": question, "answer": final_response}
            )
        st.rerun()

    @staticmethod
    def __extract_json_from_content(content_str: str) -> dict | str:
        json_pattern = r"content='(\{.*\})'"
        json_match = re.search(json_pattern, content_str, re.DOTALL)

        json_str = None
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content_str.strip()

        if json_str:
            try:
                json_obj = json.loads(json_str)
                return json_obj
            except json.JSONDecodeError as error:
                logger.error(
                    f"Streamlit Extracted string is not valid JSON: {json_str[:200]}..., error: {error}"
                )
                return content_str

        return content_str

    def __unescape_dict(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self.__unescape_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.__unescape_dict(item) for item in data]
        elif isinstance(data, str):
            return data.encode().decode("unicode_escape")
        else:
            return data
