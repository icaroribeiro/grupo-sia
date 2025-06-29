from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)


class Forward:
    async def migrate(self):
        await InvoiceItemDocument.init()


class Backward:
    async def migrate(self):
        await InvoiceItemDocument.drop_collection()
