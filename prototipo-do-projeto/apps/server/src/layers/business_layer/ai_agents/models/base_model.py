from datetime import datetime

from pydantic import BaseModel
from src.layers.core_logic_layer.logging import logger


class BaseModel(BaseModel):
    @staticmethod
    def parse_br_datetime(date_str: str) -> datetime | None:
        """Parse Brazilian datetime format (DD/MM/YYYY HH:MM:SS)"""
        if not isinstance(date_str, str) or not date_str:
            message = (
                "Error: Failed to parse Brazilian datetime string with non-string "
                "or empty string date"
            )
            logger.error(message)
            return None
        try:
            return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
        except ValueError as error:
            message = f"Error: Failed to parse {date_str} to Brazilian datetime "
            f"string: {error}"
            logger.error(message)
            return None

    @staticmethod
    def parse_br_float(value_str: str) -> float | None:
        """Parse Brazilian float format (e.g., 1.234,56)"""
        if not isinstance(value_str, str) or not value_str:
            message = "Error: Failed to parse Brazilian float string with non-string "
            "or empty string value"
            logger.error(message)
            return None
        try:
            cleaned_value = value_str.replace(".", "").replace(",", ".")
            return float(cleaned_value)
        except ValueError as error:
            message = f"Error: Failed to parse Brazilian float strings {value_str}: "
            f"{error}"
            logger.error(message)
            return None
