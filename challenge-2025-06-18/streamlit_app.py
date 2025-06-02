import asyncio
import streamlit as st
import traceback
from ai_agents_crew.crew_orchestrator import CrewOrchestrator
from ai_agents_crew.logger import logger


async def main():
    st.set_page_config(
        page_title="Assistente de Análise de Arquivos CSV do Grupo SIA",
        page_icon="🤖",
        layout="centered",
    )

    st.title("🤖 Assistente de Análise de Arquivos CSV do Grupo SIA")
    st.markdown("""
        Seja bem-vindo! Digite sua dúvida no campo abaixo e eu farei o possível para responder.
    """)

    user_question = st.text_input(
        "Faça sua pergunta aqui:",
        placeholder="Ex: Qual é o item de maior valor?",
    )

    if st.button("Obter Resposta"):
        if user_question:
            crew_orchestrator = CrewOrchestrator()
            try:
                with st.spinner("Pensando na sua resposta..."):
                    response = await crew_orchestrator.run_orchestration(
                        user_input_message=user_question
                    )
            except Exception as err:
                logger.error(f"\nAn error occurred in Crew Orchestrator: {err}")
                traceback.print_exc()
                raise
            st.success("Resposta Gerada!")
            st.write("---")
            st.subheader("Sua Pergunta:")
            st.info(user_question)
            st.subheader("Minha Resposta:")
            st.success(response)
            st.write("---")
            st.markdown("Espero ter ajudado!😊")
        else:
            st.warning(
                "Por favor, digite sua pergunta antes de clicar em 'Obter Resposta'."
            )

    st.sidebar.header("Sobre este Assistente")
    st.sidebar.info(
        """
            Esta é a interface de perguntas e respostas sobre arquivos CSV
        """
    )
    st.sidebar.markdown(
        "Desenvolvido com ❤️ pelo Grupo SIA (Soluções Inteligentes Autônomas)"
    )


if __name__ == "__main__":
    asyncio.run(main())
