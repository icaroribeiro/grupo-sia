from src.layers.data_access_layer.mongodb.repositories.base_repository import (
    BaseRepository,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)


class InvoiceItemRepository(BaseRepository[InvoiceItemDocument]):
    def __init__(self):
        super().__init__(document=InvoiceItemDocument)
