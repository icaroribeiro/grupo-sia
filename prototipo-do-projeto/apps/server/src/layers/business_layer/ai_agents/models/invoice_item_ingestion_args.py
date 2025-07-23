from typing import Type

from beanie import Document
from pydantic import BaseModel, Field

from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)


class InvoiceItemIngestionArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Path to the CSV file (format: YYYYMM_NFe_NotaFiscalItem.csv)",
    )
    document_class: Type[Document] = Field(
        default=InvoiceItemDocument, description="Beanie document class (InvoiceItem)"
    )
