import streamlit as st


class HomePage:
    def __init__(self) -> None:
        pass

    def show(self) -> None:
        st.title("🏡 Aplicativo de Análise de Dados!")
        st.markdown(
            """
            Ao enviar um arquivo .zip contendo seus conjuntos de dados, você pode:

            * **Carregar e Descompactar**: Acesse o menu **Upload** para enviar seu arquivo .zip com segurança.

            * **Conversar com um Agente**: Acesse o menu **Bate-Papo** para fazer perguntas sobre seus dados em linguagem natural.

            * **Gerar Gráficos**: Acesse o menu **Plotagem** para visualizar as principais tendências e padrões em seus dados com gráficos poderosos.
            """
        )
