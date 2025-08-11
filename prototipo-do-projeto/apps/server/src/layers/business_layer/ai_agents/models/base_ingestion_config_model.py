from pydantic import BaseModel
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import pandas as pd


class BaseIngestionConfig(BaseModel):
    file_suffix: str
    csv_columns_to_dtypes: Dict[str, type]
    csv_columns_to_model_fields: Dict[str, "ColumnMapping"]
    table_name: str

    # Protected parse methods
    @staticmethod
    def _parse_br_datetime(value: str) -> datetime:
        """Parse Brazilian datetime format to Python datetime."""
        return pd.to_datetime(value, format="%d/%m/%Y %H:%M:%S", errors="coerce")

    @staticmethod
    def _parse_br_float(value: str) -> float:
        """Parse Brazilian float format (e.g., '1.234,56') to Python float."""
        if isinstance(value, str):
            value = value.replace(".", "").replace(",", ".")
        return float(value)


# Nested model for csv_columns_to_model_fields
class ColumnMapping(BaseModel):
    field: str
    converter: Optional[Callable[[str], Any]] = None


# Ensure ColumnMapping is defined before BaseIngestionConfig resolves forward references
BaseIngestionConfig.model_rebuild()
