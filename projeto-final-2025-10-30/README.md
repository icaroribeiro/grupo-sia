# projeto-final-2025-10-30

**![Licença MIT](https://img.shields.io/badge/Licença-MIT-blue.svg)**

- [Introdução](#introdução)
- [Como configurar a aplicação?](#como-configurar-a-aplicação)
- [Como executar a aplicação?](#como-executar-a-aplicação)
- [Licença](#licença)

## Introdução

Este projeto consiste no desenvolvimento de um aplicativo que permite a classificação e gerenciamento de notas fiscais em formato CSV obtidas do [**Portal da Transparência**](https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais).

## Fluxos de Trabalho

A aplicação foi desenvolvida com base em dois fluxos de trabalho envolvendo múltiplos agentes de IA, utilizando as seguintes ferramentas: [**Python**](https://www.python.org/), os frameworks [**Streamlit**](https://streamlit.io/) e [**LangGraph**](https://www.langchain.com/langgraph) e o banco de dados
[**PostgreSQL**](https://www.postgresql.org/)

O fluxo de trabalho principal da aplicação consiste na utilização de um Agente Gerente (`manager_agent`) e dois sub fluxos de trabalho: fluxo de ingestão de dados e fluxo de análise de dados.

![texto alternativo](data/output/top_level_workflow.png)

### Fluxo de Ingestão de Dados

Este fluxo de trabalho da aplicação consiste na utilização de um Agente Supervisor (`supervisor_agent`) e três agentes especializados - o agente de pré processamento (`unzip_file_agent`), o agente de mapeamento de aruqivos CSV (`csv_mapping_agent`) e o agente de inserção de registros (`insert_records_agent`) - que trabalham em conjunto para o processamento de dados, geração de arquivos CSV mapeados e inserção de registros no banco de dados.

![texto alternativo](data/output/data_ingestion_workflow.png)

### Fluxo de Análise de Dados

Este fluxo de trabalho da aplicação consiste na utilização de um Agente Supervisor (`supervisor_agent`) e um agente especializado - o agente de análise de dados (`data_analysis_agent`) - que trabalham em conjunto para geração de respostas às perguntas de usuário, como também a formatação de dados necessários para as ferramentas gerenciais.

![texto alternativo](data/output/data_analysis_workflow.png)

## Como configurar a aplicação?

Antes de executar a aplicação localmente, é necessário instalar o [**Docker**](https://www.docker.com/) na máquina local.

Depois disso, obtenha uma chave de API OpenAI para a configuração dos Agentes de IA.

### Configurar o arquivo .env:

Renomeie o arquivo **.env.example** para **.env** e atribua valores para as chaves do arquivo conforme desejado.

Neste caso, apenas a variável relacionada a API KEY do LLM logo abaixo do comentário AI Settings é necessária. Todas as demais variáveis de ambiente podem ser mantidas sem qualquer alteração.

Por exemplo:

```
AI_LLM_API_KEY=
```

## Como executar a aplicação?

A aplicação pode ser executada usando comandos adicionados em um arquivo Makefile.

### Arquivo Makefile

Um arquivo **Makefile** foi criado como um único ponto de entrada contendo um conjunto de instruções para o desenvolvimento da aplicação.

Construção da Imagem do Contêiner do Banco de Dados

Navegue até a pasta da aplicação onde se encontra o arquivo Makefile e, ao mesmo tempo, o arquivo docker-compose.yml. Então, execute o comando de construção da imagem:

```
make startup-postgresql-container
```

Construção da Imagem do Contêiner da Aplicação

Também navegue até a pasta da aplicação onde se encontram os arquivos anteriores e execute o comando de construção da imagem:

```
make startup-streamlit-app-container
```
