from typing import Dict

from src.layers.business_layer.ai_agents.models.base_ingestion_config_model import (
    BaseIngestionConfig,
    ColumnMapping,
)


class InvoiceIngestionConfig(BaseIngestionConfig):
    file_suffix: str = "NFe_NotaFiscal"
    csv_columns_to_dtypes: Dict[str, type] = {
        "CPF/CNPJ Emitente": str,
        "INSCRIÇÃO ESTADUAL EMITENTE": str,
        "CNPJ DESTINATÁRIO": str,
        "NÚMERO PRODUTO": str,
        "CÓDIGO NCM/SH": str,
        "CFOP": str,
    }
    csv_columns_to_model_fields: Dict[str, ColumnMapping] = {
        "CHAVE DE ACESSO": ColumnMapping(field="access_key"),
        "MODELO": ColumnMapping(field="model"),
        "SÉRIE": ColumnMapping(field="series"),
        "NÚMERO": ColumnMapping(field="number"),
        "NATUREZA DA OPERAÇÃO": ColumnMapping(field="operation_nature"),
        "DATA EMISSÃO": ColumnMapping(
            field="issue_date", converter=BaseIngestionConfig._parse_br_datetime
        ),
        "EVENTO MAIS RECENTE": ColumnMapping(field="latest_event"),
        "DATA/HORA EVENTO MAIS RECENTE": ColumnMapping(
            field="latest_event_datetime",
            converter=BaseIngestionConfig._parse_br_datetime,
        ),
        "CPF/CNPJ Emitente": ColumnMapping(field="emitter_cnpj_cpf"),
        "RAZÃO SOCIAL EMITENTE": ColumnMapping(field="emitter_corporate_name"),
        "INSCRIÇÃO ESTADUAL EMITENTE": ColumnMapping(
            field="emitter_state_registration"
        ),
        "UF EMITENTE": ColumnMapping(field="emitter_uf"),
        "MUNICÍPIO EMITENTE": ColumnMapping(field="emitter_municipality"),
        "CNPJ DESTINATÁRIO": ColumnMapping(field="recipient_cnpj"),
        "NOME DESTINATÁRIO": ColumnMapping(field="recipient_name"),
        "UF DESTINATÁRIO": ColumnMapping(field="recipient_uf"),
        "INDICADOR IE DESTINATÁRIO": ColumnMapping(field="recipient_ie_indicator"),
        "DESTINO DA OPERAÇÃO": ColumnMapping(field="operation_destination"),
        "CONSUMIDOR FINAL": ColumnMapping(field="final_consumer"),
        "PRESENÇA DO COMPRADOR": ColumnMapping(field="buyer_presence"),
        "VALOR NOTA FISCAL": ColumnMapping(
            field="total_invoice_value", converter=BaseIngestionConfig._parse_br_float
        ),
    }
    table_name: str = "invoice"
