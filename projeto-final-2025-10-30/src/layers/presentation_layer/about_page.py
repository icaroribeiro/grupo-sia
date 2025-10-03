import os

import streamlit as st


class AboutPage:
    def show(self):
        st.title("ℹ️ Sobre o Aplicativo")
        st.write(
            """
            Este aplicativo foi desenvolvido com a linguagem **Python**, os frameworks 
            **Streamlit** e **LangGraph**, e um banco de dados **PostgreSQL** para ajudar 
            você a classificar e gerenciar notas fiscais em formato CSV obtidas do Portal 
            da Transparência: https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais
            """
        )
        st.write(
            """
            Ele utiliza um workflow de alto nível e dois subworkflows relacionados providos 
            de agentes de IA especializados para i) extrair, mapear e inserir dados das 
            notas fiscais no banco de dados e ii) realizar a análise de dados destes documentos 
            segundo diferentes atributos como por tipo (compra, venda, serviço) e por centros 
            de custos, e além de gerar recursos gráficos e outras visualizações, tudo isso 
            através de um simples bate-papo.
            """
        )
        file_path = "data/output/data_analysis_workflow.png"
        if os.path.exists(file_path):
            st.image(file_path, width=500, caption="Workflow de Análise de Dados")
        else:
            st.warning(f"O arquivo do workflow não foi encontrado em: {file_path}")
        st.subheader("Desenvolvido pelo **Grupo SIA** com ❤️")
        st.markdown(
            "Este aplicativo foi desenvolvido pelo integrante **Ícaro Ribeiro (icaroribeiro@hotmail.com)** "
        )
