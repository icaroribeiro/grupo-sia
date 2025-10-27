import os

import pandas as pd
import streamlit as st
from dependency_injector.wiring import Provide, inject
from src.streamlit_app_layers.settings_layer.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.streamlit_app_layers.core_layer.container.container import Container


class AboutPage:
    @inject
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings = Provide[
            Container.streamlit_app_settings
        ],
    ) -> None:
        self.streamlit_app_settings = streamlit_app_settings

    def show(self):
        st.title("ℹ️ Sobre o Sistema")
        st.write(
            """
            Este sistema foi desenvolvido com a linguagem **Python**, os frameworks 
            **Streamlit** e **LangGraph**, e um banco de dados **PostgreSQL**.
            """
        )
        st.write(
            """
            Ele utiliza um workflow provido de **Agentes de IA** especializados:
            
            * **Agente Supervisor**: O Maestro do Fluxo responsável por receber a consulta inicial 
            do usuário e decidir qual agente especializado deve assumir a tarefa.

            * **Agente de Descompactação de Arquivo ZIP**: Descompacta arquivos ZIP que contém
            arquivos de NF-e em arquivos CSV.

            * **Agente de Mapeamento de CSVs**: Mapeia dados das NF-e em arquivos CSV 
            para argumentos de ingestão que serão inseridos em tabelas no banco de dados SQL.

            * **Agente de Inserção de Registros**: Insere dados das NF-e obtidos do 
            mapeamento dos argumentos de ingestão no banco de dados SQL.

            * **Agente de Análise de Dados**: Analisa dados segundo diferentes atributos como 
            por tipo (compra, venda, serviço) e por centros de custos, e além de gerar recursos gráficos,
            tudo isso através de um simples bate-papo.
            """
        )

        file_path = f"{self.streamlit_app_settings.data_output_workflow_dir_path}/invoice_mgmt_workflow.png"
        if os.path.exists(file_path):
            st.image(
                file_path,
                caption="Fluxo de Trabalho do Sistema de Gestão de NF-e com IA",
            )
        else:
            st.warning(
                f"A imagem do Fluxo de Trabalho do Sistema de Gestão de NF-e com IA não foi encontrado em: {file_path}"
            )

        st.subheader("**Grupo SIA (Soluções Inteligentes Autônomas)**")
        team_data = [
            {
                "Membro da Equipe": "Ícaro Ribeiro",
                "Contato": "icaroribeiro@hotmail.com",
            }
        ]
        st.subheader("Integrantes:")
        df_team = pd.DataFrame(team_data)
        st.dataframe(
            df_team,
            hide_index=True,
            use_container_width=True,
        )
