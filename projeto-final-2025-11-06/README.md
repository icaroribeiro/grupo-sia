# projeto-final-2025-11-06

**![Licença MIT](https://img.shields.io/badge/Licença-MIT-blue.svg)**

- [Introdução](#introdução)
- [Artefatos](#artefatos)
- [Como configurar a aplicação?](#como-configurar-a-aplicação)
- [Como executar a aplicação?](#como-executar-a-aplicação)
- [Licença](#licença)

## Introdução

Este aplicativo foi desenvolvido para ser uma ferramenta de classificação, análise e reporte de dados de NF-e em arquivos no formato CSV obtidas do [**Portal da Transparência**](https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais).

Este aplicativo foi desenvolvido com a linguagem [**Python**](https://www.python.org/), os frameworks [**Streamlit**](https://streamlit.io/) e [**LangGraph**](https://www.langchain.com/langgraph) e o banco de dados
[**PostgreSQL**](https://www.postgresql.org/).

Ele utiliza um workflow provido de Agentes de IA especializados:

- Agente Supervisor: O Maestro do Fluxo responsável por receber a consulta inicial do usuário e decidir qual agente especializado deve assumir a tarefa.

- Agente de Descompactação de Arquivo ZIP: Descompacta arquivos ZIP que contém arquivos de NF-e em formato CSV.

- Agente de Mapeamento de CSVs: Mapeia dados das NF-e em arquivos CSV para argumentos de ingestão que serão inseridos em tabelas no banco de dados SQL.

- Agente de Inserção de Registros: Insere dados das NF-e obtidos do mapeamento dos argumentos de ingestão no banco de dados SQL.

- Agente de Análise de Dados: Analisa dados segundo diferentes atributos como por tipo (compra, venda, serviço) e por centros de custos, e além de gerar recursos gráficos e outras visualizações, tudo isso através de um simples bate-papo.

![texto alternativo](data/output/workflow/invoice_mgmt_workflow.png)

## Artefatos

Os artefatos do projeto (Relatório do Projeto, Apresentação em formato PPTX e Vídeo de apresentação para banca examinadora) estão armazenados no diretório **Projeto Final - Artefatos**.

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
