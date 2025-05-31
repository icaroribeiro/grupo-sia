import streamlit as st


def generate_response(user_question):
    return f"Entendi que você perguntou: '{user_question}'. No momento, minha capacidade é limitada, mas estou sempre aprendendo!"


def main():
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
            with st.spinner("Pensando na sua resposta..."):
                response = generate_response(user_question)
            st.success("Resposta Gerada!")
            st.write("---")
            st.subheader("Sua Pergunta:")
            st.info(user_question)
            st.subheader("Minha Resposta:")
            st.success(response)
            st.write("---")
            st.markdown("Espero ter ajudado! 😊")
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
    main()
