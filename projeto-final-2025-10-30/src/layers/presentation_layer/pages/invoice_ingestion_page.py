import asyncio
import os
import pandas as pd
import streamlit as st
from typing import List
from dependency_injector.wiring import Provide, inject
from src.layers.business_layer.ai_agents.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner


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
        if "processing_complete" not in st.session_state:
            st.session_state.processing_complete = False
        if "ingestion_complete" not in st.session_state:
            st.session_state.ingestion_complete = False

        self.streamlit_app_settings = streamlit_app_settings
        self.invoice_mgmt_workflow = invoice_mgmt_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("🗄️ Ingestão de NF-e")
        st.subheader("Upload de Arquivo, Pré-visualização e Inserção de NF-e")
        st.markdown(
            "Use a barra lateral para carregar um arquivo ZIP. O sistema irá descompactar (1ª Etapa) e exibir uma amostra dos arquivos CSV. Use o botão **'Iniciar Ingestão'** para o mapeamento e inserção no banco de dados (2ª Etapa)."
        )

        self.__render_sidebar()

        if not st.session_state.uploaded_file:
            st.info(
                "Por favor, carregue um arquivo **.zip** na barra lateral para iniciar o processamento."
            )
        elif not st.session_state.processing_complete:
            self.__run_decompress_workflow()
        else:
            self.__display_data_sample()

            if st.session_state.ingestion_complete:
                st.subheader("Inserção de Notas Fiscais")
                st.success("✅ Mapeamento e Inserção concluídos!")

    def __render_sidebar(self) -> None:
        with st.sidebar:
            st.header("1ª Etapa: Upload de Arquivo 📥")

            if not st.session_state.uploaded_file:
                self.__upload_file()
            else:
                st.info(
                    f"📁 Arquivo carregado: **{os.path.basename(st.session_state.uploaded_file)}**"
                )
                if st.button(
                    "🔄 Iniciar Nova Análise/Fazer Upload", use_container_width=True
                ):
                    self.__reset_state()
                    st.rerun()

            st.markdown("---")
            st.header("2ª Etapa: Ingestão de Documentos 🚀")

            ingestion_button_clicked = st.button(
                "▶️ Iniciar Ingestão no Banco de Dados",
                disabled=not st.session_state.processing_complete
                or st.session_state.ingestion_complete,
                use_container_width=True,
            )

            if ingestion_button_clicked:
                self.__run_ingestion_workflow()
                st.rerun()

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
                    expanded=True,
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
        st.session_state.processing_complete = False
        st.session_state.ingestion_complete = False
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
                st.session_state.processing_complete = False
                st.session_state.ingestion_complete = False
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
            - Perform ONLY the first step of the multi-step procedure: Unzip the ZIP file.
            - The ZIP file is located at '{file_path}'.
            - Unzip the file to the directory '{data_output_upload_extracted_dir_path}'.
            
            CRITICAL RULES:
            - ONLY execute the Unzip task. DO NOT proceed to CSV Mapping or Insertion.
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
            st.session_state.processing_complete = True

            status_placeholder.empty()
            st.success(
                f"✅ Descompactação **concluída**. **{len(extracted_files)}** arquivos CSV prontos para pré-visualização e ingestão!"
            )

            st.rerun()

        except Exception as error:
            message = f"Falha ao rodar o fluxo de trabalho para descompressão: {error}"
            logger.error(message, exc_info=True)
            status_placeholder.empty()
            st.error(message)

    def __run_ingestion_workflow(self):
        data_output_upload_extracted_dir_path = (
            self.streamlit_app_settings.data_output_upload_extracted_dir_path
        )
        data_output_ingestion_dir_path = (
            self.streamlit_app_settings.data_output_ingestion_dir_path
        )
        status_placeholder = st.empty()
        status_placeholder.warning(
            "⏳ Iniciando o fluxo de trabalho de **Mapeamento e Inserção** no banco de dados... (2ª Etapa)"
        )

        try:
            input_message = f"""
            INSTRUCTIONS:
            - Perform the remaining steps of the multi-step procedure: CSV Mapping and Record Insertion.
            - The extracted CSV files are located at '{data_output_upload_extracted_dir_path}'.
            - Map these files to ingestion arguments in the directory '{data_output_ingestion_dir_path}'.
            - Finally, insert records from the ingestion arguments into the database.
            
            CRITICAL RULES:
            - **STRICTLY FOLLOW THIS SEQUENCE:**
            1. **FIRST:** Delegate the task of **CSV Mapping** to the respective agent (e.g., `delegate_to_csv_mapping_agent_tool`).
            2. **THEN, AND ONLY AFTER STEP 1 IS COMPLETE:** Delegate the task of **Record Insertion** to the respective agent (`delegate_to_insert_records_agent_tool`).
            - The Mapping task must **always** precede the Insertion task.
            - The Unzip task is already complete. DO NOT re-execute the Unzip task.
            - **NEVER** output more than one tool call (handoff) in the same step.
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

            st.session_state.ingestion_complete = True
            st.session_state.processing_complete = True

            status_placeholder.empty()
            st.success("✅ Mapeamento e Inserção concluídos com sucesso!")

        except Exception as error:
            message = (
                f"Falha ao rodar o fluxo de trabalho para Mapeamento/Inserção: {error}"
            )
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
