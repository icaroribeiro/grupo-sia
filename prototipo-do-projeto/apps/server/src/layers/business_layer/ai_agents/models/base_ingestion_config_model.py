from pydantic import BaseModel
from typing import Optional, Callable, Any
from datetime import datetime
import pandas as pd


class BaseIngestionConfigModel(BaseModel):
    file_suffix: str
    csv_columns_to_dtypes: dict[str, type]
    csv_columns_to_model_fields: dict[str, "ColumnMappingModel"]
    table_name: str

    @staticmethod
    def _parse_br_datetime(value: str) -> datetime:
        return pd.to_datetime(value, format="%d/%m/%Y %H:%M:%S", errors="coerce")

    @staticmethod
    def _parse_br_float(value: str) -> float:
        if isinstance(value, str):
            value = value.replace(".", "").replace(",", ".")
        return float(value)


# Nested model for csv_columns_to_model_fields
class ColumnMappingModel(BaseModel):
    field: str
    converter: Optional[Callable[[str], Any]] = None


# Ensure ColumnMappingModel is defined before BaseIngestionConfigModel resolves forward references
BaseIngestionConfigModel.model_rebuild()
