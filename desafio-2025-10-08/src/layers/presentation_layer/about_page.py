import os

import streamlit as st


class AboutPage:
    def show(self):
        st.title("ℹ️ Sobre o Aplicativo")
        st.write(
            """
            Este aplicativo foi desenvolvido com a linguagem **Python**, os frameworks 
            **Streamlit** e **LangGraph**, e um banco de dados PostgreSQL para ajudar você a 
            analisar e compreender quaisquer dados de um arquivo CSV compactado em um arquivo `.zip`.
            """
        )
        st.write(
            """
            A solução utiliza um fluxo de trabalho provido de agentes de IA especializados para realizar a 
            Análise Exploratória de Dados (A.E.D.), detectando padrões, identificando anomalias 
            e gerando visualizações, tudo isso através de um simples bate-papo.
            """
        )
        file_path = "data/output/data_analysis_workflow.png"
        if os.path.exists(file_path):
            st.image(file_path, width=500, caption="Fluxo de Trabalho da Solução")
        else:
            st.warning(f"O arquivo do workflow não foi encontrado em: {file_path}")
        st.markdown(
            "Este aplicativo foi desenvolvido por **Ícaro Ribeiro** (icaroribeiro@hotmail.com), integrante do **Grupo SIA**."
        )
