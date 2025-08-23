from src.layers.business_layer.ai_agents.models.base_ingestion_config_model import (
    BaseIngestionConfigModel,
    ColumnMappingModel,
)


class InvoiceIngestionConfig(BaseIngestionConfigModel):
    file_suffix: str = "NFe_NotaFiscal"
    csv_columns_to_model_fields: dict[str, ColumnMappingModel] = {
        "CHAVE DE ACESSO": ColumnMappingModel(field="access_key"),
        "MODELO": ColumnMappingModel(field="model"),
        "SÉRIE": ColumnMappingModel(field="series"),
        "NÚMERO": ColumnMappingModel(field="number"),
        "NATUREZA DA OPERAÇÃO": ColumnMappingModel(field="operation_nature"),
        "DATA EMISSÃO": ColumnMappingModel(
            field="issue_date", converter=BaseIngestionConfigModel._parse_br_datetime
        ),
        "EVENTO MAIS RECENTE": ColumnMappingModel(field="latest_event"),
        "DATA/HORA EVENTO MAIS RECENTE": ColumnMappingModel(
            field="latest_event_datetime",
            converter=BaseIngestionConfigModel._parse_br_datetime,
        ),
        "CPF/CNPJ Emitente": ColumnMappingModel(field="emitter_cnpj_cpf"),
        "RAZÃO SOCIAL EMITENTE": ColumnMappingModel(field="emitter_corporate_name"),
        "INSCRIÇÃO ESTADUAL EMITENTE": ColumnMappingModel(
            field="emitter_state_registration"
        ),
        "UF EMITENTE": ColumnMappingModel(field="emitter_uf"),
        "MUNICÍPIO EMITENTE": ColumnMappingModel(field="emitter_municipality"),
        "CNPJ DESTINATÁRIO": ColumnMappingModel(field="recipient_cnpj"),
        "NOME DESTINATÁRIO": ColumnMappingModel(field="recipient_name"),
        "UF DESTINATÁRIO": ColumnMappingModel(field="recipient_uf"),
        "INDICADOR IE DESTINATÁRIO": ColumnMappingModel(field="recipient_ie_indicator"),
        "DESTINO DA OPERAÇÃO": ColumnMappingModel(field="operation_destination"),
        "CONSUMIDOR FINAL": ColumnMappingModel(field="final_consumer"),
        "PRESENÇA DO COMPRADOR": ColumnMappingModel(field="buyer_presence"),
        "VALOR NOTA FISCAL": ColumnMappingModel(
            field="total_invoice_value",
            converter=BaseIngestionConfigModel._parse_br_float,
        ),
    }
    table_name: str = "invoice"
    model_fields_to_dtypes: dict[str, type] = {
        "emitter_cnpj_cpf": str,
        "emitter_state_registration": str,
        "recipient_cnpj": str,
        "product_number": str,
        "ncm_sh_code": str,
        "cfop": str,
    }
