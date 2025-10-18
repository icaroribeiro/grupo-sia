from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.layers.data_access_layer.db.postgresql.models.base_model import BaseModel


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
    def from_data(cls, data: dict[str, Any]) -> "InvoiceItemModel":
        return cls(
            # Denormalized Invoice Header Fields
            access_key=cls.assign_value(data=data, key="access_key", type_=String),
            model=cls.assign_value(data=data, key="model", type_=String),
            series=cls.assign_value(data=data, key="series", type_=Integer),
            number=cls.assign_value(data=data, key="number", type_=Integer),
            operation_nature=cls.assign_value(
                data=data, key="operation_nature", type_=String
            ),
            issue_date=cls.assign_value(data=data, key="issue_date", type_=DateTime),
            emitter_cnpj_cpf=cls.assign_value(
                data=data, key="emitter_cnpj_cpf", type_=String
            ),
            emitter_corporate_name=cls.assign_value(
                data=data, key="emitter_corporate_name", type_=String
            ),
            emitter_state_registration=cls.assign_value(
                data=data, key="emitter_state_registration", type_=String
            ),
            emitter_uf=cls.assign_value(data=data, key="emitter_uf", type_=String),
            emitter_municipality=cls.assign_value(
                data=data, key="emitter_municipality", type_=String
            ),
            recipient_cnpj=cls.assign_value(
                data=data, key="recipient_cnpj", type_=String
            ),
            recipient_name=cls.assign_value(
                data=data, key="recipient_name", type_=String
            ),
            recipient_uf=cls.assign_value(data=data, key="recipient_uf", type_=String),
            recipient_ie_indicator=cls.assign_value(
                data=data, key="recipient_ie_indicator", type_=String
            ),
            operation_destination=cls.assign_value(
                data=data, key="operation_destination", type_=String
            ),
            final_consumer=cls.assign_value(
                data=data, key="final_consumer", type_=String
            ),
            buyer_presence=cls.assign_value(
                data=data, key="buyer_presence", type_=String
            ),
            # Item-Specific Fields
            product_number=cls.assign_value(
                data=data, key="product_number", type_=String
            ),
            product_service_description=cls.assign_value(
                data=data, key="product_service_description", type_=String
            ),
            ncm_sh_code=cls.assign_value(data=data, key="ncm_sh_code", type_=String),
            ncm_sh_product_type=cls.assign_value(
                data=data, key="ncm_sh_product_type", type_=String
            ),
            cfop=cls.assign_value(data=data, key="cfop", type_=String),
            quantity=cls.assign_value(data=data, key="quantity", type_=Numeric),
            unit=cls.assign_value(data=data, key="unit", type_=String),
            unit_value=cls.assign_value(data=data, key="unit_value", type_=Numeric),
            total_value=cls.assign_value(data=data, key="total_value", type_=Numeric),
        )
