from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.db.models.base_model import (
    BaseModel,
)


class InvoiceModel(BaseModel):
    __tablename__ = "invoices"

    access_key: Mapped[str] = mapped_column(
        String(44),
        unique=True,
        comment="Unique access key for the invoice (CHAVE DE ACESSO)",
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
    latest_event: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Most recent event (EVENTO MAIS RECENTE)"
    )
    latest_event_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date/time of latest event (DATA/HORA EVENTO MAIS RECENTE)",
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
        String(2), nullable=False, comment="Recipient's UF (UF DESTINATÁRIO)"
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
    total_invoice_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Total invoice value (VALOR NOTA FISCAL)",
    )

    @classmethod
    def get_table_name(cls) -> str:
        return cls.__tablename__

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "InvoiceModel":
        return cls(
            access_key=cls.assign_value(data=data, key="access_key", type_=String),
            model=cls.assign_value(data=data, key="model", type_=String),
            series=cls.assign_value(data=data, key="series", type_=Integer),
            number=cls.assign_value(data=data, key="number", type_=Integer),
            operation_nature=cls.assign_value(
                data=data, key="operation_nature", type_=String
            ),
            issue_date=cls.assign_value(data=data, key="issue_date", type_=DateTime),
            latest_event=cls.assign_value(data=data, key="latest_event", type_=String),
            latest_event_datetime=cls.assign_value(
                data=data, key="latest_event_datetime", type_=DateTime
            ),
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
            total_invoice_value=cls.assign_value(
                data=data, key="total_invoice_value", type_=Numeric
            ),
        )
