from pydantic import Field

from src.layers.data_access_layer.mongodb.documents.base_document import BaseDocument


class InvoiceDocument(BaseDocument):
    access_key: str = Field(..., unique=True, alias="chave_de_acesso")

    class Settings:
        name = "nota_fiscal"
        indexes = ["chave_de_acesso"]
