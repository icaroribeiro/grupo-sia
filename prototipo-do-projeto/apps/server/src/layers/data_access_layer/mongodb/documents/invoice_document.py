from datetime import datetime
from typing import Annotated, Any

from beanie import Indexed
from pydantic import Field

from src.layers.data_access_layer.mongodb.documents.base_document import BaseDocument


class InvoiceDocument(BaseDocument):
    access_key: Annotated[str, Indexed(unique=True)] = Field(
        ...,
        alias="chave_de_acesso",
        description="Unique access key for the invoice (CHAVE DE ACESSO)",
    )
    model: str = Field(..., alias="modelo", description="Type of invoice (MODELO)")
    series: int = Field(..., alias="serie", description="Invoice series (SÉRIE)")
    number: int = Field(..., alias="numero", description="Invoice number (NÚMERO)")
    operation_nature: str = Field(
        ...,
        alias="natureza_da_operacao",
        description="Nature of the operation (NATUREZA DA OPERAÇÃO)",
    )
    issue_date: datetime = Field(
        ..., alias="data_emissao", description="Date of issue (DATA EMISSÃO)"
    )
    latest_event: str = Field(
        ...,
        alias="evento_mais_recente",
        description="Most recent event (EVENTO MAIS RECENTE)",
    )
    latest_event_datetime: datetime = Field(
        ...,
        alias="data_hora_evento_mais_recente",
        description="Date/time of latest event (DATA/HORA EVENTO MAIS RECENTE)",
    )
    emitter_cnpj_cpf: str = Field(
        ...,
        alias="cpf_cnpj_emitente",
        description="Emitter's CPF/CNPJ (CPF/CNPJ Emitente)",
    )
    emitter_corporate_name: str = Field(
        ...,
        alias="razao_social_emitente",
        description="Emitter's corporate name (RAZÃO SOCIAL EMITENTE)",
    )
    emitter_state_registration: str = Field(
        ...,
        alias="inscricao_estadual_emitente",
        description="Emitter's State Registration (INSCRIÇÃO ESTADUAL EMITENTE)",
    )
    emitter_uf: str = Field(
        ...,
        alias="uf_emitente",
        description="Emitter's UF (UF EMITENTE)",
    )
    emitter_municipality: str = Field(
        ...,
        alias="municipio_emitente",
        description="Emitter's municipality (MUNICÍPIO EMITENTE)",
    )
    recipient_cnpj: str = Field(
        ...,
        alias="cnpj_destinatario",
        description="Recipient's CNPJ (CNPJ DESTINATÁRIO)",
    )
    recipient_name: str = Field(
        ...,
        alias="nome_destinatario",
        description="Recipient's name (NOME DESTINATÁRIO)",
    )
    recipient_uf: str = Field(
        ...,
        alias="uf_destinatario",
        description="Recipient's UF (UF DESTINATÁRIO)",
    )
    recipient_ie_indicator: str = Field(
        ...,
        alias="indicador_ie_destinatario",
        description="Recipient's IE indicator (INDICADOR IE DESTINATÁRIO)",
    )
    operation_destination: str = Field(
        ...,
        alias="destino_da_operacao",
        description="Operation destination (DESTINO DA OPERAÇÃO)",
    )
    final_consumer: str = Field(
        ...,
        alias="consumidor_final",
        description="Final consumer indicator (CONSUMIDOR FINAL)",
    )
    buyer_presence: str = Field(
        ...,
        alias="presenca_do_comprador",
        description="Buyer presence indicator (PRESENÇA DO COMPRADOR)",
    )
    total_invoice_value: float = Field(
        ...,
        alias="valor_nota_fiscal",
        description="Total invoice value (VALOR NOTA FISCAL)",
    )

    class Settings:
        name = "nota_fiscal"

    @classmethod
    def get_csv_columns_to_dtypes(cls) -> dict[str, str]:
        return {
            "CPF/CNPJ Emitente": str,
            "INSCRIÇÃO ESTADUAL EMITENTE": str,
            "CNPJ DESTINATÁRIO": str,
        }

    @classmethod
    def get_csv_columns_to_document_fields(cls) -> dict[str, dict[str, Any]]:
        return {
            "CHAVE DE ACESSO": {"field": "access_key"},
            "MODELO": {"field": "model"},
            "SÉRIE": {"field": "series"},
            "NÚMERO": {"field": "number"},
            "NATUREZA DA OPERAÇÃO": {"field": "operation_nature"},
            "DATA EMISSÃO": {
                "field": "issue_date",
                "converter": cls.parse_br_datetime,
            },
            "EVENTO MAIS RECENTE": {"field": "latest_event"},
            "DATA/HORA EVENTO MAIS RECENTE": {
                "field": "latest_event_datetime",
                "converter": cls.parse_br_datetime,
            },
            "CPF/CNPJ Emitente": {"field": "emitter_cnpj_cpf"},
            "RAZÃO SOCIAL EMITENTE": {"field": "emitter_corporate_name"},
            "INSCRIÇÃO ESTADUAL EMITENTE": {"field": "emitter_state_registration"},
            "UF EMITENTE": {"field": "emitter_uf"},
            "MUNICÍPIO EMITENTE": {"field": "emitter_municipality"},
            "CNPJ DESTINATÁRIO": {"field": "recipient_cnpj"},
            "NOME DESTINATÁRIO": {"field": "recipient_name"},
            "UF DESTINATÁRIO": {"field": "recipient_uf"},
            "INDICADOR IE DESTINATÁRIO": {"field": "recipient_ie_indicator"},
            "DESTINO DA OPERAÇÃO": {"field": "operation_destination"},
            "CONSUMIDOR FINAL": {"field": "final_consumer"},
            "PRESENÇA DO COMPRADOR": {"field": "buyer_presence"},
            "VALOR NOTA FISCAL": {
                "field": "total_invoice_value",
                "converter": cls.parse_br_float,
            },
        }
