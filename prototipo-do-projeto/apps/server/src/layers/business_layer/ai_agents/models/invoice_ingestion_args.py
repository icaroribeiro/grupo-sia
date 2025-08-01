# from typing import Type

# from pydantic import BaseModel, Field

# from src.layers.data_access_layer.postgresdb.models.invoice_model import InvoiceModel


# class InvoiceIngestionArgs(BaseModel):
#     file_path: str = Field(
#         ...,
#         description="Path to the CSV file (format: YYYYMM_NFe_NotaFiscal.csv)",
#     )
#     model_class: Type[InvoiceModel] = Field(
#         default=InvoiceModel, description="SQLAlchemy InvoiceModel class."
#     )
