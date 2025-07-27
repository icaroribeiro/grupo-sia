from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.layers.data_access_layer.postgresdb.models.base_model import BaseModel
from typing import Any
from sqlalchemy import UniqueConstraint


class InvoiceItemModel(BaseModel):
    """
    Represents a single item within an invoice, with denormalized header data.
    """

    __tablename__ = "invoice_item"
    __table_args__ = (
        UniqueConstraint(
            "access_key",
            "product_number",
            name="uq_invoice_item_access_key_product_number",
        ),
    )

    # Denormalized Invoice Header Fields
    access_key: Mapped[str] = mapped_column(
        String(44),
        ForeignKey("invoice.access_key", ondelete="CASCADE"),
        nullable=False,
        comment="Invoice access key (CHAVE DE ACESSO)",
    )
    model: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Type of invoice (MODELO)"
    )
    series: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Invoice series (SÉRIE)"
    )
    number: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Invoice number (NÚMERO)"
    )
    operation_nature: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nature of the operation (NATUREZA DA OPERAÇÃO)",
    )
    issue_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date of issue (DATA EMISSÃO)",
    )
    emitter_cnpj_cpf: Mapped[str] = mapped_column(
        String(14),
        nullable=False,
        comment="Emitter's CPF/CNPJ (CPF/CNPJ Emitente)",
    )
    emitter_corporate_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Emitter's corporate name (RAZÃO SOCIAL EMITENTE)",
    )
    emitter_state_registration: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Emitter's State Registration (INSCRIÇÃO ESTADUAL EMITENTE)",
    )
    emitter_uf: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="Emitter's UF (UF EMITENTE)",
    )
    emitter_municipality: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Emitter's municipality (MUNICÍPIO EMITENTE)",
    )
    recipient_cnpj: Mapped[str] = mapped_column(
        String(14),
        nullable=False,
        comment="Recipient's CNPJ (CNPJ DESTINATÁRIO)",
    )
    recipient_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Recipient's name (NOME DESTINATÁRIO)",
    )
    recipient_uf: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="Recipient's UF (UF DESTINATÁRIO)",
    )
    recipient_ie_indicator: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Recipient's IE indicator (INDICADOR IE DESTINATÁRIO)",
    )
    operation_destination: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Operation destination (DESTINO DA OPERAÇÃO)",
    )
    final_consumer: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Final consumer indicator (CONSUMIDOR FINAL)",
    )
    buyer_presence: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Buyer presence indicator (PRESENÇA DO COMPRADOR)",
    )
    # Item-Specific Fields
    product_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Product number (NÚMERO PRODUTO)",
    )
    product_service_description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Product/Service description (DESCRIÇÃO DO PRODUTO/SERVIÇO)",
    )
    ncm_sh_code: Mapped[str] = mapped_column(
        String(8), nullable=False, comment="NCM/SH code (CÓDIGO NCM/SH)"
    )
    ncm_sh_product_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="NCM/SH product type (NCM/SH (TIPO DE PRODUTO))",
    )
    cfop: Mapped[str] = mapped_column(
        String(4), nullable=False, comment="CFOP code (CFOP)"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Quantity (QUANTIDADE)",
    )
    unit: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Unit of measure (UNIDADE)"
    )
    unit_value: Mapped[Decimal] = mapped_column(
        Numeric(21, 10),
        nullable=False,
        comment="Unit value (VALOR UNITÁRIO)",
    )
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Total value of the item (VALOR TOTAL)",
    )

    @classmethod
    def get_table_name(cls) -> str:
        return cls.__tablename__

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
