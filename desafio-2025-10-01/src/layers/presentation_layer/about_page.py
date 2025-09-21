import streamlit as st


class AboutPage:
    def show(self):
        st.title("ℹ️ Sobre o Aplicativo")
        st.write(
            """
            Este aplicativo foi desenvolvido para ajudar você a analisar e compreender quaisquer dados 
            de um arquivo CSV compactado em um arquivo `.zip`.
            """
        )
        st.write(
            """
            Ele utiliza agentes de IA especializados para realizar Análise Exploratória de Dados (EDA), 
            detectar padrões, identificar anomalias e gerar visualizações, tudo isso através de um 
            simples bate-papo.
            """
        )
        st.subheader("Desenvolvido por")
        st.markdown("O aplicativo é um projeto do **Grupo SIA** com ❤️")
