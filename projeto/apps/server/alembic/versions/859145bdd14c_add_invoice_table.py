"""add_invoice_table

Revision ID: 859145bdd14c
Revises: 01a16669352f
Create Date: 2025-07-25 08:37:05.589011

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "859145bdd14c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates the invoice table."""

    op.create_table(
        "invoice",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Unique UUID identifier for the invoice",
        ),
        sa.Column(
            "access_key",
            sa.String(length=44),
            primary_key=True,
            nullable=False,
            unique=True,
            comment="Unique access key for the invoice (CHAVE DE ACESSO)",
        ),
        sa.Column(
            "model",
            sa.String(length=51),
            nullable=False,
            comment="Type of invoice (MODELO)",
        ),
        sa.Column(
            "series", sa.Integer, nullable=False, comment="Invoice series (SÉRIE)"
        ),
        sa.Column(
            "number", sa.Integer, nullable=False, comment="Invoice number (NÚMERO)"
        ),
        sa.Column(
            "operation_nature",
            sa.String(length=255),
            nullable=False,
            comment="Nature of the operation (NATUREZA DA OPERAÇÃO)",
        ),
        sa.Column(
            "issue_date",
            sa.DateTime,
            nullable=False,
            comment="Date of issue (DATA EMISSÃO)",
        ),
        sa.Column(
            "latest_event",
            sa.String(length=255),
            nullable=False,
            comment="Most recent event (EVENTO MAIS RECENTE)",
        ),
        sa.Column(
            "latest_event_datetime",
            sa.DateTime,
            nullable=False,
            comment="Date/time of latest event (DATA/HORA EVENTO MAIS RECENTE)",
        ),
        sa.Column(
            "emitter_cnpj_cpf",
            sa.String(length=14),
            nullable=False,
            comment="Emitter's CPF/CNPJ (CPF/CNPJ Emitente)",
        ),
        sa.Column(
            "emitter_corporate_name",
            sa.String(length=255),
            nullable=False,
            comment="Emitter's corporate name (RAZÃO SOCIAL EMITENTE)",
        ),
        sa.Column(
            "emitter_state_registration",
            sa.String(length=20),
            nullable=False,
            comment="Emitter's State Registration (INSCRIÇÃO ESTADUAL EMITENTE)",
        ),
        sa.Column(
            "emitter_uf",
            sa.String(length=2),
            nullable=False,
            comment="Emitter's UF (UF EMITENTE)",
        ),
        sa.Column(
            "emitter_municipality",
            sa.String(length=100),
            nullable=False,
            comment="Emitter's municipality (MUNICÍPIO EMITENTE)",
        ),
        sa.Column(
            "recipient_cnpj",
            sa.String(length=14),
            nullable=False,
            comment="Recipient's CNPJ (CNPJ DESTINATÁRIO)",
        ),
        sa.Column(
            "recipient_name",
            sa.String(length=255),
            nullable=False,
            comment="Recipient's name (NOME DESTINATÁRIO)",
        ),
        sa.Column(
            "recipient_uf",
            sa.String(length=2),
            nullable=False,
            comment="Recipient's UF (UF DESTINATÁRIO)",
        ),
        sa.Column(
            "recipient_ie_indicator",
            sa.String(length=50),
            nullable=False,
            comment="Recipient's IE indicator (INDICADOR IE DESTINATÁRIO)",
        ),
        sa.Column(
            "operation_destination",
            sa.String(length=50),
            nullable=False,
            comment="Operation destination (DESTINO DA OPERAÇÃO)",
        ),
        sa.Column(
            "final_consumer",
            sa.String(length=50),
            nullable=False,
            comment="Final consumer indicator (CONSUMIDOR FINAL)",
        ),
        sa.Column(
            "buyer_presence",
            sa.String(length=50),
            nullable=False,
            comment="Buyer presence indicator (PRESENÇA DO COMPRADOR)",
        ),
        sa.Column(
            "total_invoice_value",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
            comment="Total invoice value (VALOR NOTA FISCAL)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp when the record was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp when the record was last updated",
        ),
    )


def downgrade() -> None:
    """Drops the invoice table."""
    op.drop_table("invoice")
