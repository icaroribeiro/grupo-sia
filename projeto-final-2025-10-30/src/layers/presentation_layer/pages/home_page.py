import streamlit as st


class HomePage:
    def __init__(self) -> None:
        pass

    def show(self) -> None:
        st.title("🏡 Gestão de NF-e com IA")
        st.subheader("Seja bem-vindo(a) ao aplicativo de Gestão de NF-e com IA")
        st.write(
            """
            Este aplicativo foi desenvolvido para trabalhar com NF-e em arquivos no formato CSV 
            obtidas do Portal da Transparência: https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais
            
            O sistema permite a descompactação, mapeamento e inserção de registros em um banco
            de dados SQL, como também a análise de dados e geração de recursos gráficos 
            e outras visualizações, como também formulação de conclusões baseadas 
            em perguntas de usuário.

            Acesse os seguintes menus à esquerda para realizar as seguintes operações:
            
            * 🗄️ **Ingestão de NF-e**: Faça o envio de seu arquivo .zip que contém as NF-e
            para decompactar, mapear e inserir seus dados em um banco de dados.

            * 📊 **Análise de Dados**: Visualize a distribuição e o resumo dos dados das NF-e e
            seus itens já inseridos no banco de dados, permitindo a exploração visual das tabelas
            disponíveis.

            * 💬 **Bate-Papo**: Faça perguntas sobre seus dados em linguagem natural e
            solicite a geração de gráficos para visualizar as principais tendências e 
            padrões em seus dados.

            * ℹ️ **Sobre**: Encontre informações adicionais e créditos sobre a aplicação, 
            as tecnologias utilizadas e a equipe de desenvolvimento.
            """
        )
