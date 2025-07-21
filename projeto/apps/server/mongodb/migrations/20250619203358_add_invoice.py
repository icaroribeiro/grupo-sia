from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)


class Forward:
    async def migrate(self):
        await InvoiceDocument.init()


class Backward:
    async def migrate(self):
        await InvoiceDocument.drop_collection()
