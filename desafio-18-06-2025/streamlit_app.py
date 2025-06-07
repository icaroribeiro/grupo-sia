import asyncio
import traceback
import os
import shutil
import streamlit as st

from ai_agents_crew.crew_orchestrator import CrewOrchestrator
from ai_agents_crew.llms import get_llm
from ai_agents_crew.logger.logger import logger


def set_page_config():
    st.set_page_config(
        page_title="Assistente de Processamento de Notas Fiscais do Grupo SIA",
        page_icon="🤖",
        layout="centered",
    )


def set_intro():
    st.title("🤖 Assistente de Processamento de Notas Fiscais do Grupo SIA")
    st.markdown("""
        Seja bem-vindo! Submeta um arquivo, digite sua dúvida e eu farei o possível para respondê-la.
    """)


def clean_data_directory(data_dir="data"):
    try:
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
            logger.info(f"Cleaned data directory: {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Created data directory: {data_dir}")
    except Exception as err:
        logger.error(f"An error occurred when cleaning data directory: {err}")
        raise


async def set_user_action():
    if "show_uploader" not in st.session_state:
        st.session_state.show_uploader = False

    def set_show_uploader():
        st.session_state.show_uploader = True

    st.button("Submeter arquivo .zip", on_click=set_show_uploader)

    if st.session_state.show_uploader:
        uploaded_file = st.file_uploader(
            "Submeta arquivo .zip", type=["zip"], key="zip_uploader"
        )
        if uploaded_file is not None:
            try:
                clean_data_directory()

                file_path = os.path.join("data", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                logger.info(f"Saved uploaded file: {file_path}")
                st.success(f"Arquivo '{uploaded_file.name}' submetido com sucesso!")
            except Exception as err:
                logger.error(f"An error occurred when uploading file: {err}")
                st.error(f"Error: {err}")

    user_query = st.text_input(
        "Faça sua pergunta aqui:",
        placeholder="Ex: Qual é o item de maior valor?",
    )

    if st.button("Obter Resposta"):
        if user_query:
            llm = get_llm()
            crew_orchestrator = CrewOrchestrator()
            try:
                with st.spinner("Pensando na sua resposta..."):
                    response = await crew_orchestrator.run_orchestration(
                        llm=llm, user_query=user_query
                    )
            except Exception as err:
                logger.error(f"An error occurred in Crew Orchestrator: {err}")
                traceback.print_exc()
                raise
            st.success("Resposta Gerada!")
            st.write("---")
            st.subheader("Sua Pergunta:")
            st.info(user_query)
            st.subheader("Minha Resposta:")
            st.success(response)
            st.write("---")
            st.markdown("Espero ter ajudado!😊")
        else:
            st.warning(
                "Por favor, digite sua pergunta antes de clicar em 'Obter Resposta'."
            )


def set_about():
    st.sidebar.header("Sobre este Assistente")
    st.sidebar.info(
        """
            Esta é a interface de perguntas e respostas sobre o processamento de Notas Fiscais
        """
    )
    st.sidebar.markdown(
        "Desenvolvido com ❤️ pelo Grupo SIA (Soluções Inteligentes Autônomas)"
    )


async def main():
    set_page_config()
    set_intro()
    await set_user_action()
    set_about()


if __name__ == "__main__":
    asyncio.run(main())
