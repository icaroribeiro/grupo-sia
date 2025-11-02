import streamlit as st


class HomePage:
    def __init__(self) -> None:
        pass

    def show(self) -> None:
        st.title("🏡 Sistema de Gestão de NF-e com IA")
        st.markdown("### Seja bem-vindo(a) ao Sistema de Gestão de NF-e com IA")
        st.write(
            """
            Este sistema foi desenvolvido para classificar, analisar e reportar dados de arquivos de NF-e em formato CSV
            obtidas do Portal da Transparência: https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais
            
            O sistema permite a descompactação, mapeamento e inserção de registros em um banco
            de dados SQL, como também a análise de dados e geração de recursos gráficos, 
            como também formulação de conclusões baseadas em perguntas de usuário.

            Acesse os seguintes menus à esquerda para obter informações e realizar operações:

            * 💾 **Modelagem de Dados**: Veja detalhes sobre tabelas e esquemas utilizados para lidar
            com mecanismo de memória e persistência, como também os dados das NF-e e seus respectivos items.
            
            * 🗄️ **Ingestão de NF-e**: Selecione um arquivo .zip contendo as NF-e
            para ser descompactado. Em seguida, faça o mapeamento das NF-e e a inserção de
            seus dados no banco de dados.

            * 📊 **Análise de Dados**: Visualize a distribuição e o resumo dos dados das NF-e e
            seus itens já inseridos no banco de dados, permitindo a exploração visual das tabelas
            disponíveis.

            * 💬 **Bate-Papo**: Faça perguntas sobre seus dados em linguagem natural e
            solicite a geração de recursos gráficos (ex. gráficos de barra e histogramas) 
            para visualizar as principais tendências e padrões em seus dados.

            * ℹ️ **Sobre**: Encontre informações adicionais e créditos sobre a aplicação, 
            as tecnologias utilizadas e a equipe de desenvolvimento.
            """
        )
