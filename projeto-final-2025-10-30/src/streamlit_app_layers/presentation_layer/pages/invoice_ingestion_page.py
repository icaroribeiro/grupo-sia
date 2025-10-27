import asyncio
import os
import pandas as pd
import streamlit as st
from typing import List
from dependency_injector.wiring import Provide, inject
from src.streamlit_app_layers.ai_layer.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.streamlit_app_layers.core_layer.container.container import Container
from src.streamlit_app_layers.core_layer.logging import logger
from src.streamlit_app_layers.settings_layer.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.streamlit_app_layers.ai_layer.workflow_runner import WorkflowRunner


class InvoiceIngestionPage:
    @inject
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings = Provide[
            Container.streamlit_app_settings
        ],
        invoice_mgmt_workflow: InvoiceMgmtWorkflow = Provide[
            Container.invoice_mgmt_workflow
        ],
        workflow_runner: WorkflowRunner = Provide[Container.workflow_runner],
    ) -> None:
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = ""
        if "extracted_csv_paths" not in st.session_state:
            st.session_state.extracted_csv_paths = []
        if "decompress_complete" not in st.session_state:
            st.session_state.decompress_complete = False
        if "mapping_complete" not in st.session_state:
            st.session_state.mapping_complete = False
        if "inserting_complete" not in st.session_state:
            st.session_state.inserting_complete = False

        self.streamlit_app_settings = streamlit_app_settings
        self.invoice_mgmt_workflow = invoice_mgmt_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("🗄️ Ingestão de NF-e")
        st.markdown("### Upload de Arquivo, Mapeamento de Colunas e Inserção no Banco")
        st.markdown(
            "O processo de ingestão é dividido em **três etapas**: "
            "1. **Upload & Descompressão** (na barra lateral), "
            "2. **Mapeamento de Colunas** e "
            "3. **Inserção no Banco de Dados**."
        )

        self.__render_sidebar()

        if not st.session_state.uploaded_file:
            st.info(
                "Por favor, carregue um arquivo **.zip** na barra lateral para iniciar o processamento."
            )
        elif not st.session_state.decompress_complete:
            self.__run_decompress_workflow()
        else:
            self.__display_data_sample()

            if not st.session_state.mapping_complete:
                st.info(
                    "Clique no botão **'Iniciar Mapeamento'** na barra lateral (2ª Etapa) para processar as colunas dos arquivos CSV."
                )
            elif not st.session_state.inserting_complete:
                st.info(
                    "Mapeamento concluído. Clique em **'Iniciar Inserção'** na barra lateral (3ª Etapa) para finalizar."
                )
            else:
                st.subheader("Inserção de Notas Fiscais")
                st.success("✅ Processo completo! Mapeamento e Inserção concluídos.")

    def __render_sidebar(self) -> None:
        with st.sidebar:
            # --- 1ª Etapa: Upload & Descompressão ---
            st.header("1ª Etapa: Upload & Descompressão 📥")

            if not st.session_state.uploaded_file:
                self.__upload_file()
            else:
                st.info(
                    f"📁 Arquivo carregado: **{os.path.basename(st.session_state.uploaded_file)}**"
                )
                if st.button(
                    "🔄 Iniciar Novo Processo/Fazer Upload", use_container_width=True
                ):
                    self.__reset_state()
                    st.rerun()

            # --- 2ª Etapa: Mapeamento ---
            st.markdown("---")
            st.header("2ª Etapa: Mapeamento de Colunas 🧭")

            mapping_button_clicked = st.button(
                "▶️ Iniciar Mapeamento",
                disabled=not st.session_state.decompress_complete
                or st.session_state.mapping_complete,
                use_container_width=True,
            )

            if mapping_button_clicked:
                self.__run_mapping_workflow()
                st.rerun()

            if st.session_state.mapping_complete:
                st.success("✅ Mapeamento de Colunas concluído!")

            # --- 3ª Etapa: Inserção ---
            st.markdown("---")
            st.header("3ª Etapa: Inserção no Banco de Dados 🚀")

            inserting_button_clicked = st.button(
                "🔥 Iniciar Inserção",
                disabled=not st.session_state.mapping_complete
                or st.session_state.inserting_complete,
                use_container_width=True,
            )

            if inserting_button_clicked:
                self.__run_inserting_workflow()
                st.rerun()

            if st.session_state.inserting_complete:
                st.success("✅ Inserção no Banco concluída!")

    def __display_data_sample(self):
        csv_paths: List[str] = st.session_state.extracted_csv_paths

        if not csv_paths:
            st.error(
                "Nenhum arquivo CSV encontrado para pré-visualização. Por favor, reinicie a análise."
            )
            return

        st.subheader("Pré-visualização de Dados Descompactados")
        st.success(
            f"✅ Descompactação concluída! Encontrados **{len(csv_paths)}** arquivos CSV para pré-visualização."
        )

        for csv_path in csv_paths:
            filename = os.path.basename(csv_path)

            try:
                dataframe = pd.read_csv(
                    filepath_or_buffer=csv_path,
                    sep=";",
                    encoding="cp1252",
                )

                num_records = len(dataframe)

                with st.expander(
                    f"📂 Arquivo: **{filename}** ({num_records} registros)",
                    expanded=False,
                ):
                    if num_records == 0:
                        st.warning(
                            "⚠️ **Arquivo Vazio:** O arquivo foi encontrado, mas não contém registros de dados."
                        )
                        st.markdown(
                            f"Colunas encontradas: **{', '.join(dataframe.columns.tolist())}**"
                        )
                    else:
                        st.markdown(
                            f"Primeiras **{len(dataframe.head(10))} linhas** de um total de **{num_records} registros**:"
                        )

                        st.dataframe(dataframe.head(10), width="stretch")

                        st.markdown("---")
                        st.markdown("**Tipos de Colunas:**")
                        dtype_df = dataframe.dtypes.rename("Tipo").to_frame()
                        dtype_df["Tipo"] = dtype_df["Tipo"].astype(str)

                        st.dataframe(dtype_df, width="stretch")

            except pd.errors.EmptyDataError:
                st.error(
                    f"❌ **Erro de Leitura:** O arquivo **{filename}** está vazio ou inválido."
                )
                logger.warning(f"EmptyDataError encountered for file: {csv_path}")
            except Exception as error:
                st.error(f"❌ Erro ao ler ou exibir o arquivo **{filename}**: {error}")
                logger.error(f"Error reading CSV in {csv_path}: {error}")

    def __reset_state(self):
        st.session_state.uploaded_file = ""
        st.session_state.decompress_complete = False
        st.session_state.mapping_complete = False
        st.session_state.inserting_complete = False
        st.session_state.extracted_csv_paths = []

    def __upload_file(self):
        zip_file = st.file_uploader("📤 Carregar um arquivo .zip", type=["zip"])

        if zip_file is not None:
            try:
                self.__delete_non_hidden_files(
                    dir_path=self.streamlit_app_settings.data_input_upload_dir_path
                )
                self.__delete_non_hidden_files(
                    dir_path=self.streamlit_app_settings.data_output_upload_extracted_dir_path
                )
                self.__delete_non_hidden_files(
                    dir_path=self.streamlit_app_settings.data_output_ingestion_dir_path
                )

                file_path = os.path.join(
                    self.streamlit_app_settings.data_input_upload_dir_path,
                    zip_file.name,
                )
                with open(file_path, "wb") as f:
                    f.write(zip_file.getbuffer())

                st.session_state.uploaded_file = file_path
                st.session_state.decompress_complete = False
                st.session_state.mapping_complete = False
                st.session_state.inserting_complete = False
                st.session_state.extracted_csv_paths = []
                st.success(f"Successfully submitted .zip file!: {zip_file.name}")
                st.rerun()

            except Exception as error:
                message = f"Failed to save ZIP archive: {error}"
                logger.error(message)
                st.error(message)

    def __run_decompress_workflow(self):
        file_path = st.session_state.uploaded_file
        data_output_upload_extracted_dir_path = (
            self.streamlit_app_settings.data_output_upload_extracted_dir_path
        )

        status_placeholder = st.empty()
        status_placeholder.info(
            "⏳ Iniciando o fluxo de trabalho para **descompactar** os dados... (1ª Etapa)"
        )

        try:
            input_message = f"""
            INSTRUCTIONS:
            - Unzip the ZIP file located in {file_path} to the directory '{data_output_upload_extracted_dir_path}.
            """

            asyncio.run(
                self.workflow_runner.run_workflow(
                    self.invoice_mgmt_workflow,
                    input_message,
                    st.session_state.session_thread_id
                    if "session_thread_id" in st.session_state
                    else "dummy_thread_id",
                )
            )

            extracted_files = [
                os.path.join(data_output_upload_extracted_dir_path, f)
                for f in os.listdir(data_output_upload_extracted_dir_path)
                if f.endswith(".csv")
            ]

            if not extracted_files:
                raise FileNotFoundError(
                    "Nenhum arquivo CSV encontrado após a descompressão. Certifique-se de que o ZIP contém arquivos CSV."
                )

            st.session_state.extracted_csv_paths = extracted_files
            st.session_state.decompress_complete = True

            status_placeholder.empty()
            st.success(
                f"✅ Descompactação **concluída**. **{len(extracted_files)}** arquivos CSV prontos para Mapeamento!"
            )

            st.rerun()

        except Exception as error:
            message = f"Falha ao rodar o fluxo de trabalho para descompressão: {error}"
            logger.error(message, exc_info=True)
            status_placeholder.empty()
            st.error(message)

    def __run_mapping_workflow(self):
        data_output_upload_extracted_dir_path = (
            self.streamlit_app_settings.data_output_upload_extracted_dir_path
        )
        data_output_ingestion_dir_path = (
            self.streamlit_app_settings.data_output_ingestion_dir_path
        )
        status_placeholder = st.empty()
        status_placeholder.info(
            "⏳ Iniciando o fluxo de trabalho de **Mapeamento de Colunas**... (2ª Etapa)"
        )

        try:
            input_message = f"""
            INSTRUCTIONS:
            - Map the extracted CSV files located in '{data_output_upload_extracted_dir_path}' to ingestion arguments and save the mapping results to the directory '{data_output_ingestion_dir_path}'. DO NOT perform the database insertion yet.
            """

            asyncio.run(
                self.workflow_runner.run_workflow(
                    self.invoice_mgmt_workflow,
                    input_message,
                    st.session_state.session_thread_id
                    if "session_thread_id" in st.session_state
                    else "dummy_thread_id",
                )
            )

            st.session_state.mapping_complete = True
            st.session_state.decompress_complete = True

            status_placeholder.empty()
            st.success("✅ Mapeamento de Colunas concluído com sucesso!")

            st.rerun()

        except Exception as error:
            message = f"Falha ao rodar o fluxo de trabalho para Mapeamento: {error}"
            logger.error(message, exc_info=True)
            status_placeholder.empty()
            st.error(message)

    def __run_inserting_workflow(self):
        data_output_ingestion_dir_path = (
            self.streamlit_app_settings.data_output_ingestion_dir_path
        )
        status_placeholder = st.empty()
        status_placeholder.warning(
            "⏳ Iniciando o fluxo de trabalho de **Inserção no Banco de Dados**... (3ª Etapa)"
        )

        try:
            input_message = f"""
            INSTRUCTIONS:
            - Insert records into the database using the mapped ingestion arguments found in the directory '{data_output_ingestion_dir_path}'.
            """

            asyncio.run(
                self.workflow_runner.run_workflow(
                    self.invoice_mgmt_workflow,
                    input_message,
                    st.session_state.session_thread_id
                    if "session_thread_id" in st.session_state
                    else "dummy_thread_id",
                )
            )

            st.session_state.inserting_complete = True
            st.session_state.mapping_complete = True

            status_placeholder.empty()
            st.success("✅ Inserção no Banco de Dados concluída com sucesso!")

            st.rerun()

        except Exception as error:
            message = f"Falha ao rodar o fluxo de trabalho para Inserção: {error}"
            logger.error(message, exc_info=True)
            status_placeholder.empty()
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
