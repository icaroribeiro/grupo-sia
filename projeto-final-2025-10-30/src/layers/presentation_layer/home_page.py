import streamlit as st


class HomePage:
    def __init__(self) -> None:
        pass

    def show(self) -> None:
        st.title(
            "🏡 Bem-vindo ao Aplicativo de Classificação e Gerenciamento de Notas Fiscais!"
        )
        st.write(
            """
            Este aplicativo foi desenvolvido como uma solução genérica para trabalhar 
            com qualquer arquivo CSV, fornecendo respostas a perguntas de usuário, como
            também gerar gráficos e apresentar conclusões.

            Acesse o menu **A.E.D. (Análise Exploratória de Dados)** para realizar as
            seguintes operações:
            
            * **Enviar e Descompactar um Arquivo ZIP**: Solicite o envio seu arquivo .zip para análise de dados.

            * **Conversar com um Agente**: Faça perguntas sobre seus dados em linguagem natural.

            * **Gerar Gráficos**: Gere gráficos para visualizar as principais tendências e padrões em seus dados.
            """
        )
