"""add_invoice_item_table

Revision ID: 1657037f60b6
Revises: 859145bdd14c
Create Date: 2025-07-25 08:37:13.573531

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "1657037f60b6"
down_revision: Union[str, Sequence[str], None] = "859145bdd14c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates the denormalized invoice_item table with a composite unique constraint."""
    op.create_table(
        "invoice_item",
        # Invoice Header Fields (denormalized)
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Unique UUID identifier for the invoice item",
        ),
        sa.Column(
            "access_key",
            sa.String(length=44),
            sa.ForeignKey("invoice.access_key", ondelete="CASCADE"),
            nullable=False,
            comment="Invoice access key (CHAVE DE ACESSO)",
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
        # Item-Specific Fields
        sa.Column(
            "product_number",
            sa.String(length=20),
            nullable=False,
            comment="Product number (NÚMERO PRODUTO)",
        ),
        sa.Column(
            "product_service_description",
            sa.String(length=255),
            nullable=False,
            comment="Product/Service description (DESCRIÇÃO DO PRODUTO/SERVIÇO)",
        ),
        sa.Column(
            "ncm_sh_code",
            sa.String(length=8),
            nullable=False,
            comment="NCM/SH code (CÓDIGO NCM/SH)",
        ),
        sa.Column(
            "ncm_sh_product_type",
            sa.String(length=255),
            nullable=True,
            comment="NCM/SH product type (NCM/SH (TIPO DE PRODUTO))",
        ),
        sa.Column(
            "cfop", sa.String(length=4), nullable=False, comment="CFOP code (CFOP)"
        ),
        sa.Column(
            "quantity",
            sa.Numeric(precision=15, scale=4),
            nullable=False,
            comment="Quantity (QUANTIDADE)",
        ),
        sa.Column(
            "unit",
            sa.String(length=10),
            nullable=False,
            comment="Unit of measure (UNIDADE)",
        ),
        sa.Column(
            "unit_value",
            sa.Numeric(precision=21, scale=10),
            nullable=False,
            comment="Unit value (VALOR UNITÁRIO)",
        ),
        sa.Column(
            "total_value",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
            comment="Total value of the item (VALOR TOTAL)",
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
        sa.UniqueConstraint(
            "access_key",
            "product_number",
            name="uq_invoice_item_access_key_product_number",
        ),
    )


def downgrade() -> None:
    """Drops the invoice_item table."""
    op.drop_table("invoice_item")
