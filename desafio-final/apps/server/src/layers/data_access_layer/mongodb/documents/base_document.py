from datetime import datetime, timedelta, timezone

from beanie import Document, PydanticObjectId
from bson import ObjectId
from pydantic import Field

from src.layers.core_logic_layer.settings.mongodb_settings import (
    get_mongodb_settings,
)


class BaseDocument(Document):
    id: PydanticObjectId = Field(default_factory=ObjectId, alias="_id")
    created_at: datetime = Field(
        default=datetime.now(tz=timezone.utc), alias="data_criacao"
    )
    updated_at: datetime = Field(
        default=datetime.now(tz=timezone.utc), alias="data_atualizacao"
    )

    async def pre_save(self):
        """Update the updated_at timestamp before saving."""

        self.updated_at = datetime.now(tz=timezone.utc)
        return await self.save()

    class Settings:
        """Common settings for all documents."""

        use_state_management = True
        validate_on_save = True
        use_cache = True
        cache_expiration_time = timedelta(
            seconds=get_mongodb_settings().cache_expiration_time_in_seconds
        )
        cache_capacity = get_mongodb_settings().cache_capacity
