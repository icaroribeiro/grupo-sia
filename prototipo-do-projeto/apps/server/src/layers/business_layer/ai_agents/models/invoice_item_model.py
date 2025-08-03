from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from src.layers.business_layer.ai_agents.models.base_model import BaseModel


class InvoiceItemModel(BaseModel):
    access_key: str = Field(
        ..., max_length=44, description="Invoice access key (CHAVE DE ACESSO)"
    )
    model: str = Field(..., max_length=51, description="Type of invoice (MODELO)")
    series: int = Field(..., description="Invoice series (SÉRIE)")
    number: int = Field(..., description="Invoice number (NÚMERO)")
    operation_nature: str = Field(
        ...,
        max_length=255,
        description="Nature of the operation (NATUREZA DA OPERAÇÃO)",
    )
    issue_date: datetime = Field(..., description="Date of issue (DATA EMISSÃO)")
    emitter_cnpj_cpf: str = Field(
        ..., max_length=14, description="Emitter's CPF/CNPJ (CPF/CNPJ Emitente)"
    )
    emitter_corporate_name: str = Field(
        ...,
        max_length=255,
        description="Emitter's corporate name (RAZÃO SOCIAL EMITENTE)",
    )
    emitter_state_registration: str = Field(
        ...,
        max_length=20,
        description="Emitter's State Registration (INSCRIÇÃO ESTADUAL EMITENTE)",
    )
    emitter_uf: str = Field(..., max_length=2, description="Emitter's UF (UF EMITENTE)")
    emitter_municipality: str = Field(
        ..., max_length=100, description="Emitter's municipality (MUNICÍPIO EMITENTE)"
    )
    recipient_cnpj: str = Field(
        ..., max_length=14, description="Recipient's CNPJ (CNPJ DESTINATÁRIO)"
    )
    recipient_name: str = Field(
        ..., max_length=255, description="Recipient's name (NOME DESTINATÁRIO)"
    )
    recipient_uf: str = Field(
        ..., max_length=2, description="Recipient's UF (UF DESTINATÁRIO)"
    )
    recipient_ie_indicator: str = Field(
        ...,
        max_length=50,
        description="Recipient's IE indicator (INDICADOR IE DESTINATÁRIO)",
    )
    operation_destination: str = Field(
        ..., max_length=50, description="Operation destination (DESTINO DA OPERAÇÃO)"
    )
    final_consumer: str = Field(
        ..., max_length=50, description="Final consumer indicator (CONSUMIDOR FINAL)"
    )
    buyer_presence: str = Field(
        ...,
        max_length=50,
        description="Buyer presence indicator (PRESENÇA DO COMPRADOR)",
    )
    product_number: str = Field(
        ..., max_length=20, description="Product number (NÚMERO PRODUTO)"
    )
    product_service_description: str = Field(
        ...,
        max_length=255,
        description="Product/Service description (DESCRIÇÃO DO PRODUTO/SERVIÇO)",
    )
    ncm_sh_code: str = Field(
        ..., max_length=8, description="NCM/SH code (CÓDIGO NCM/SH)"
    )
    ncm_sh_product_type: str | None = Field(
        ...,
        max_length=255,
        description="NCM/SH product type (NCM/SH (TIPO DE PRODUTO))",
    )
    cfop: str = Field(..., max_length=4, description="CFOP code (CFOP)")
    quantity: Decimal = Field(..., description="Quantity (QUANTIDADE)")
    unit: str = Field(..., max_length=10, description="Unit of measure (UNIDADE)")
    unit_value: Decimal = Field(..., description="Unit value (VALOR UNITÁRIO)")
    total_value: Decimal = Field(
        ..., description="Total value of the item (VALOR TOTAL)"
    )

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
    def get_csv_columns_to_model_fields(cls) -> dict[str, dict[str, Any]]:
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
