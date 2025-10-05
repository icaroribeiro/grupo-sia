import os
import streamlit as st
from dependency_injector.wiring import Provide, inject
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)


class UploadTestPage:
    @inject
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings = Provide[
            Container.streamlit_app_settings
        ],
    ) -> None:
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = ""

        self.streamlit_app_settings = streamlit_app_settings

    def show(self) -> None:
        st.title("✅ Validação Simples de Upload de Arquivo")
        st.info(
            "Carregue um arquivo .zip na barra lateral para testar se ele é salvo no disco com sucesso."
        )

        with st.sidebar:
            st.header("Upload de Arquivo (ZIP) 📥")

            if not st.session_state.uploaded_file:
                self._render_file_uploader()
            else:
                file_name = os.path.basename(st.session_state.uploaded_file)
                st.success("🎉 Upload **VALIDADO** com sucesso!")
                st.markdown(f"**Arquivo salvo em disco:** `{file_name}`")

                if st.button("🔄 Iniciar Novo Teste/Fazer Upload"):
                    st.session_state.uploaded_file = ""
                    st.rerun()

        if st.session_state.uploaded_file:
            st.balloons()
            st.markdown(
                "O arquivo foi salvo! Clique em **'Iniciar Novo Teste/Fazer Upload'** na barra lateral para limpar o estado."
            )
        else:
            st.warning("Aguardando o upload de um arquivo.")

    def _render_file_uploader(self):
        zip_file = st.file_uploader("📤 Carregar um arquivo .zip", type=["zip"])

        if zip_file is not None:
            try:
                upload_data_dir_path = self.streamlit_app_settings.upload_data_dir_path
                self.__delete_non_hidden_files(dir_path=upload_data_dir_path)
                file_path = os.path.join(upload_data_dir_path, zip_file.name)
                with open(file_path, "wb") as f:
                    f.write(zip_file.getbuffer())
                st.session_state.uploaded_file = file_path
                st.rerun()

            except Exception as error:
                message = f"Falha ao salvar o arquivo ZIP: {error}"
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
            message = f"Falha ao limpar o diretório: {error}"
            logger.error(message)
            st.error(message)
