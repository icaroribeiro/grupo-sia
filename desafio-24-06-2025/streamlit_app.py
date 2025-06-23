import asyncio
import os
import shutil
import traceback

import streamlit as st

from ai_agents_crew.crew_orchestrator import CrewOrchestrator
from ai_agents_crew.llms import get_llm
from ai_agents_crew.logger.logger import logger
from ai_agents_crew.settings.settings import get_settings


def set_page_config():
    st.set_page_config(
        page_title="Assistente de Notas Fiscais - Grupo SIA",
        page_icon="🤖",
        layout="centered",
    )


def set_intro():
    st.title("Assistente de Notas Fiscais - Grupo SIA")
    st.markdown(
        "Seja bem-vindo! Submeta um arquivo .zip com notas fiscais e pergunte o que quiser!"
    )


def set_llm():
    try:
        st.session_state.llm = get_llm()
    except Exception as err:
        logger.error(f"Erro ao carregar a chave de API: {err}")
        st.error("Chave de API não configurada!")


async def handle_user_action():
    if "uploaded_file_path" not in st.session_state:
        st.session_state.uploaded_file_path = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = list()
    if "cached_dataframes_dict_dict" not in st.session_state:
        st.session_state.cached_dataframes_dict_dict = dict()

    if not st.session_state.uploaded_file_path:
        uploaded_file = st.file_uploader("📤 Envie um arquivo .zip", type=["zip"])
        if uploaded_file is not None:
            try:
                if not get_settings().DATA_DIR:
                    st.error("Diretório de dados não configurado!")
                data_dir = get_settings().DATA_DIR

                try:
                    if os.path.exists(data_dir):
                        shutil.rmtree(data_dir)
                    os.makedirs(data_dir)
                except Exception:
                    st.error(
                        f"Erro ao criar diretório '{data_dir}' para armazenar arquivos .zip"
                    )

                file_path = os.path.join(data_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success(f"Arquivo .zip submetido com sucesso!: {uploaded_file.name}")
                st.session_state.uploaded_file_path = file_path
                st.session_state.cached_dataframes_dict = dict()
                st.session_state.chat_history = list()
                st.rerun()
            except Exception as err:
                logger.error(f"Erro ao salvar o arquivo .zip: {err}")
                st.error(f"Erro: {err}")
        return
    else:
        st.info(f"📁 Arquivo .zip carregado: {st.session_state.uploaded_file_path}")
        if st.button("📄 Enviar novo arquivo .zip"):
            st.session_state.uploaded_file_path = ""
            st.session_state.cached_dataframes_dict = dict()
            st.session_state.chat_history = list()
            st.rerun()

    await set_chat_history()


async def set_chat_history():
    for message in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(message["pergunta"])
        with st.chat_message("assistant"):
            st.markdown(message["resposta"])

    if prompt := st.chat_input("Digite sua pergunta..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            with st.spinner("💡 Gerando resposta..."):
                crew_orchestrator = CrewOrchestrator()
                is_ok, response = await crew_orchestrator.run_orchestration(
                    llm=st.session_state.llm,
                    user_query=prompt,
                    file_path=st.session_state.uploaded_file_path,
                    cached_dataframes_dict=st.session_state.cached_dataframes_dict,
                )
                if not is_ok:
                    st.error(response)
        except Exception as err:
            logger.error(
                f"An error occurred when processing user query: {err}", exc_info=True
            )
            traceback.print_exc()
            response = "⚠️ Ocorreu um erro ao processar sua pergunta."

        st.session_state.chat_history.append({"pergunta": prompt, "resposta": response})

        with st.chat_message("assistant"):
            st.markdown(response)


def set_about():
    st.sidebar.header("ℹ️ Sobre")
    st.sidebar.info(
        "Este assistente processa notas fiscais em arquivos .zip e responde perguntas com base nos dados extraídos."
    )
    st.sidebar.markdown("Desenvolvido por **Grupo SIA** com ❤️")


async def main():
    set_page_config()
    set_intro()
    set_llm()
    await handle_user_action()
    set_about()


if __name__ == "__main__":
    asyncio.run(main())
