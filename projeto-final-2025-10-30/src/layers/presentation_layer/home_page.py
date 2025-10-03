import streamlit as st


class HomePage:
    def __init__(self) -> None:
        pass

    def show(self) -> None:
        st.title("🏡 Aplicativo de Classificação e Gerenciamento de Notas Fiscais!")
        st.write(
            """
            Este aplicativo foi desenvolvido como uma solução para trabalhar com notas fiscais 
            em formato CSV, possibilitando a análise de dados e geração de recursos gráficos e outras visualizações,
            como também formulação de conclusões baseadas em perguntas de usuário.

            Acesse o menu **Bate-Papo** para realizar as seguintes operações:
            
            * **Enviar e Descompactar um Arquivo ZIP**: Solicite o envio seu arquivo .zip para análise de dados.

            * **Conversar com um Agente**: Faça perguntas sobre seus dados em linguagem natural.

            * **Gerar Gráficos**: Gere gráficos para visualizar as principais tendências e padrões em seus dados.
            """
        )
