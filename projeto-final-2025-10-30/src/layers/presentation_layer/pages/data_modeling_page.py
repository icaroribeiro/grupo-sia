import streamlit as st


class DataModelingPage:
    def __init__(self) -> None:
        pass

    def show(self) -> None:
        st.title("💾 Modelagem de Dados")
        st.markdown("### Memória e Persistência do Agente de IA")
        st.write(
            """
            Para manter o contexto e a memória das conversas no menu **💬 Bate-Papo**, o sistema emprega um mecanismo 
            de **Checkpointing** (ponto de verificação) no banco de dados PostgreSQL, utilizando o componente 
            `AsyncPostgresSaver` (do LangGraph/LangChain).
            
            Isso garante a **persistência do estado** de cada workflow (thread), permitindo que as interações 
            sejam retomadas em caso de falha ou simplesmente ao retornar à mesma thread.
            
            O estado de cada conversação é salvo nas seguintes tabelas de metadados:
            """
        )

        st.markdown(
            """
            * **`checkpoints`**: Armazena os **instantâneos de estado (snapshots)** das threads de conversação. 
              Cada registro contém o estado interno completo do agente de IA em um determinado ponto de execução.
            * **`checkpoint_blobs`**: Usada para armazenar dados binários ou grandes estruturas de dados associadas 
              aos checkpoints, que são separadas da tabela principal para otimizar o desempenho.
            * **`checkpoint_writes`**: Tabela de rastreamento usada para auxiliar na consistência transacional e 
              garantir a atomicidade durante a escrita de novos checkpoints.
            * **`checkpoint_migrations`**: Tabela de controle de versão que registra quais alterações de esquema 
              foram aplicadas às tabelas de checkpoint.
            """
        )

        st.markdown("---")

        st.markdown("### Modelagem de Dados de NF-e")
        st.write(
            """
            O sistema utiliza um esquema relacional **desnormalizado** com duas tabelas principais (`invoice` e `invoice_item`) 
            com colunas correspondentes aos dados de arquivos CSV obtidos do Portal da Transparência para armazenar os dados das NF-e.
            
            A tabela `invoice_item` está ligada à tabela `invoice` através da **`access_key` (Chave de Acesso)**, 
            e não pelo ID primário UUID. Esta é uma relação de **um-para-muitos (1:N)**.
            """
        )

        st.markdown("#### 1. Tabela `invoice` (Cabeçalho da Fatura)")
        st.markdown(
            "Esta tabela armazena os dados principais e os participantes da Nota Fiscal (NF-e). **Chave Primária Composta:** (`id`, `access_key`)."
        )

        invoice_schema = {
            "Coluna": [
                "id",
                "access_key",
                "model",
                "series",
                "number",
                "operation_nature",
                "issue_date",
                "latest_event",
                "latest_event_datetime",
                "emitter_cnpj_cpf",
                "emitter_corporate_name",
                "emitter_state_registration",
                "emitter_uf",
                "emitter_municipality",
                "recipient_cnpj",
                "recipient_name",
                "recipient_uf",
                "recipient_ie_indicator",
                "operation_destination",
                "final_consumer",
                "buyer_presence",
                "total_invoice_value",
                "created_at",
                "updated_at",
            ],
            "Tipo de Dado (PostgreSQL)": [
                "UUID (PK)",
                "VARCHAR(44) (PK/Unique)",
                "VARCHAR(51)",
                "INTEGER",
                "INTEGER",
                "VARCHAR(255)",
                "DATETIME",
                "VARCHAR(255)",
                "DATETIME",
                "VARCHAR(14)",
                "VARCHAR(255)",
                "VARCHAR(20)",
                "VARCHAR(2)",
                "VARCHAR(100)",
                "VARCHAR(14)",
                "VARCHAR(255)",
                "VARCHAR(2)",
                "VARCHAR(50)",
                "VARCHAR(50)",
                "VARCHAR(50)",
                "VARCHAR(50)",
                "NUMERIC(15, 2)",
                "DATETIME (TZ)",
                "DATETIME (TZ)",
            ],
            "Descrição (Comentário)": [
                "Identificador UUID único",
                "Chave de acesso única (CHAVE DE ACESSO)",
                "Tipo de nota fiscal (MODELO)",
                "Série da nota fiscal (SÉRIE)",
                "Número da nota fiscal (NÚMERO)",
                "Natureza da operação (NATUREZA DA OPERAÇÃO)",
                "Data de emissão (DATA EMISSÃO)",
                "Evento mais recente (EVENTO MAIS RECENTE)",
                "Data/hora do evento mais recente",
                "CPF/CNPJ do emitente",
                "Razão social do emitente",
                "Inscrição Estadual do emitente",
                "UF do emitente",
                "Município do emitente",
                "CNPJ do destinatário",
                "Nome do destinatário",
                "UF do destinatário",
                "Indicador IE do destinatário",
                "Destino da operação",
                "Indicador de consumidor final",
                "Indicador de presença do comprador",
                "Valor total da nota fiscal",
                "Timestamp de criação do registro",
                "Timestamp da última atualização do registro",
            ],
        }

        st.dataframe(invoice_schema, use_container_width=True)

        st.markdown("#### 2. Tabela `invoice_item` (Itens da Fatura)")
        st.markdown(
            "Esta tabela é desnormalizada e armazena os detalhes dos produtos e serviços, ligada à `invoice` pela `access_key`. **Chave Primária:** (`id`)."
        )
        st.info(
            "A unicidade é garantida pela combinação (`access_key`, `product_number`)."
        )

        invoice_item_data = {
            "Coluna": [
                "id",
                "access_key",
                "model",
                "series",
                "number",
                "operation_nature",
                "issue_date",
                "emitter_cnpj_cpf",
                "emitter_corporate_name",
                "emitter_state_registration",
                "emitter_uf",
                "emitter_municipality",
                "recipient_cnpj",
                "recipient_name",
                "recipient_uf",
                "recipient_ie_indicator",
                "operation_destination",
                "final_consumer",
                "buyer_presence",
                "product_number",
                "product_service_description",
                "ncm_sh_code",
                "ncm_sh_product_type",
                "cfop",
                "quantity",
                "unit",
                "unit_value",
                "total_value",
                "created_at",
                "updated_at",
            ],
            "Tipo de Dado (PostgreSQL)": [
                "UUID (PK)",
                "VARCHAR(44) (FK)",
                "VARCHAR(51)",
                "INTEGER",
                "INTEGER",
                "VARCHAR(255)",
                "DATETIME",
                "VARCHAR(14)",
                "VARCHAR(255)",
                "VARCHAR(20)",
                "VARCHAR(2)",
                "VARCHAR(100)",
                "VARCHAR(14)",
                "VARCHAR(255)",
                "VARCHAR(2)",
                "VARCHAR(50)",
                "VARCHAR(50)",
                "VARCHAR(50)",
                "VARCHAR(50)",
                "VARCHAR(20)",
                "VARCHAR(255)",
                "VARCHAR(8)",
                "VARCHAR(255)",
                "VARCHAR(4)",
                "NUMERIC(15, 4)",
                "VARCHAR(10)",
                "NUMERIC(21, 10)",
                "NUMERIC(15, 2)",
                "DATETIME (TZ)",
                "DATETIME (TZ)",
            ],
            "Descrição (Comentário)": [
                "Identificador UUID único do item",
                "Chave de Acesso da Fatura",
                "Modelo da NF-e",
                "Série da NF-e",
                "Número da NF-e",
                "Natureza da Operação",
                "Data de Emissão",
                "CPF/CNPJ do Emitente",
                "Razão Social do Emitente",
                "Inscrição Estadual do Emitente",
                "UF do Emitente",
                "Município do Emitente",
                "CNPJ do Destinatário",
                "Nome do Destinatário",
                "UF do Destinatário",
                "Indicador IE do Destinatário",
                "Destino da Operação",
                "Consumidor Final",
                "Presença do Comprador",
                "Número do Produto",
                "Descrição do Produto/Serviço",
                "Código NCM/SH",
                "Tipo de Produto NCM/SH",
                "Código CFOP",
                "Quantidade",
                "Unidade de Medida",
                "Valor Unitário",
                "Valor Total do Item",
                "Timestamp de criação do registro",
                "Timestamp da última atualização do registro",
            ],
        }
        st.dataframe(invoice_item_data, use_container_width=True)

        st.markdown("### Detalhes Relacionais e Chaves")
        st.markdown(
            """
            #### Chaves Primárias (`PK` - Primary Key)
            * **`invoice`**: Chave Primária Composta por **`id`** e **`access_key`**.
            * **`invoice_item`**: Chave Primária **`id`**.
            
            #### Chave Estrangeira (`FK` - Foreign Key)
            * **`invoice_item.access_key`** referencia **`invoice.access_key`**.
            
            #### Restrição de Unicidade
            * **`invoice`**: **`access_key`** é única na tabela de faturas.
            * **`invoice_item`**: Existe uma restrição de unicidade composta por **(`access_key`, `product_number`)** para garantir que a combinação de fatura e item seja única.
            """
        )
