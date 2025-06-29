from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.repositories.base_repository import (
    BaseRepository,
)


class InvoiceRepository(BaseRepository[InvoiceDocument]):
    def __init__(self):
        super().__init__(document=InvoiceDocument)
