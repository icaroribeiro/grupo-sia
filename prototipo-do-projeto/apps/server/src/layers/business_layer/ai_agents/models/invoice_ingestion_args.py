from typing import Type

from beanie import Document
from pydantic import BaseModel, Field

from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)


class InvoiceIngestionArgs(BaseModel):
    file_path: str = Field(
        ...,
        description="Path to the CSV file (format: YYYYMM_NFe_NotaFiscal.csv)",
    )
    document_class: Type[Document] = Field(
        default=InvoiceDocument, description="Beanie document class (Invoice)"
    )
