# from typing import Type

# from pydantic import BaseModel, Field

# from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
#     InvoiceItemModel,
# )


# class InvoiceItemIngestionArgs(BaseModel):
#     file_path: str = Field(
#         ...,
#         description="Path to the CSV file (format: YYYYMM_NFe_NotaFiscalItem.csv)",
#     )
#     model_class: Type[InvoiceItemModel] = Field(
#         default=InvoiceItemModel, description="SQLAlchemy InvoiceItemModel class."
#     )
