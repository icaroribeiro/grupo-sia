from datetime import datetime, timedelta, timezone

from beanie import Document, PydanticObjectId
from bson import ObjectId
from pydantic import Field

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.mongodb_settings import (
    MongoDBSettings,
)

mongodb_settings = MongoDBSettings()


class BaseDocument(Document):
    id: PydanticObjectId = Field(default_factory=ObjectId, alias="_id")
    created_at: datetime = Field(
        default=datetime.now(tz=timezone.utc), alias="data_criacao"
    )
    updated_at: datetime = Field(
        default=datetime.now(tz=timezone.utc), alias="data_atualizacao"
    )

    async def pre_save(self):
        self.updated_at = datetime.now(tz=timezone.utc)
        return await self.save()

    class Settings:
        use_state_management = True
        validate_on_save = True
        use_cache = True
        cache_expiration_time = timedelta(
            seconds=mongodb_settings.cache_expiration_time_in_seconds
        )
        cache_capacity = mongodb_settings.cache_capacity

    @staticmethod
    def parse_br_datetime(date_str: str) -> datetime | None:
        if not isinstance(date_str, str) or not date_str:
            message = "Got an error when parsing Brazilian datetime string with non-string or empty string date"
            logger.error(message)
            return None
        try:
            return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
        except ValueError as error:
            message = f"Got an error when parsing {date_str} to Brazilian datetime string: {error}"
            logger.error(message)
            return None

    def parse_br_float(value_str: str) -> float | None:
        if not isinstance(value_str, str) or not value_str:
            message = "Got an error when parsing Brazilian float string with non-string or empty string value"
            logger.error(message)
            return None
        try:
            cleaned_value = value_str.replace(".", "").replace(",", ".")
            return float(cleaned_value)
        except ValueError as error:
            message = f"Got an error when parsing Brazilian float strings {value_str}: {error}"
            logger.error(message)
            return None
