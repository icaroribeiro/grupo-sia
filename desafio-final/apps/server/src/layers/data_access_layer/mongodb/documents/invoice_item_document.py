from datetime import datetime
from typing import Annotated, Any

from beanie import Indexed
from pydantic import Field

from src.layers.data_access_layer.mongodb.documents.base_document import BaseDocument


class InvoiceItemDocument(BaseDocument):
    access_key: Annotated[str, Indexed(unique=True)] = Field(
        ...,
        alias="chave_de_acesso",
        description="Unique access key for the invoice item (CHAVE DE ACESSO)",
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
    product_number: str = Field(
        ...,
        alias="número_produto",
        description="Product number (NÚMERO PRODUTO)",
    )
    product_service_description: str = Field(
        ...,
        alias="descrição_do_produto_serviço",
        description="Product/Service description (DESCRIÇÃO DO PRODUTO/SERVIÇO)",
    )
    ncm_sh_code: str = Field(
        ...,
        alias="código_ncm_sh",
        description="NCM/SH code (CÓDIGO NCM/SH)",
    )
    ncm_sh_product_type: str = Field(
        ...,
        alias="ncm_sh_tipo_de_produto",
        description="NCM/SH product type (NCM/SH (TIPO DE PRODUTO))",
    )
    cfop: str = Field(
        ...,
        alias="cfop",
        description="CFOP code (CFOP)",
    )
    quantity: float = Field(
        ...,
        alias="quantidade",
        description="Quantity (QUANTIDADE)",
    )
    unit: str = Field(
        ...,
        alias="unidade",
        description="Unit of measure (UNIDADE)",
    )
    unit_value: float = Field(
        ...,
        alias="valor_unitário",
        description="Unit value (VALOR UNITÁRIO)",
    )
    total_value: float = Field(
        ...,
        alias="valor_total",
        description="Total value of the item (VALOR TOTAL)",
    )

    class Settings:
        name = "nota_fiscal_item"

    @classmethod
    def get_csv_columns_to_dtypes(cls) -> dict[str, str]:
        return {
            "CPF/CNPJ Emitente": str,
            "INSCRIÇÃO ESTADUAL EMITENTE": str,
            "CNPJ DESTINATÁRIO": str,
            "NÚMERO PRODUTO": str,
            "CÓDIGO NCM/SH": str,
            "CFOP": str,
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
            "NÚMERO PRODUTO": {"field": "product_number"},
            "DESCRIÇÃO DO PRODUTO/SERVIÇO": {"field": "product_service_description"},
            "CÓDIGO NCM/SH": {"field": "ncm_sh_code"},
            "NCM/SH (TIPO DE PRODUTO)": {"field": "ncm_sh_product_type"},
            "CFOP": {"field": "cfop"},
            "QUANTIDADE": {"field": "quantity", "converter": cls.parse_br_float},
            "UNIDADE": {"field": "unit"},
            "VALOR UNITÁRIO": {"field": "unit_value", "converter": cls.parse_br_float},
            "VALOR TOTAL": {"field": "total_value", "converter": cls.parse_br_float},
        }
