import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.layers.core_logic_layer.logging import logger


class BaseModel(AsyncAttrs, DeclarativeBase):
    """Base class for SQLAlchemy models"""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, name="id"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    async def pre_save(self, session: AsyncSession) -> None:
        """Update timestamp before saving"""
        self.updated_at = datetime.now(tz=timezone.utc)
        await session.merge(self)

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
