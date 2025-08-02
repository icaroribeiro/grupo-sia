from decimal import Decimal
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from enum import Enum

from sqlalchemy import (
    Float,
    Integer,
    Numeric,
    String,
)


class SQLAlchemyType(Enum):
    INTEGER = Integer
    FLOAT = Float
    STRING = String
    DATETIME = DateTime
    NUMERIC = Numeric


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
    def assign_value(
        data: dict[str, Any], key: str, type_: Any
    ) -> int | float | str | datetime | Decimal | None:
        value = data.get(key, None)
        if value is None:
            match type_:
                case SQLAlchemyType.INTEGER.value:
                    return 0
                case SQLAlchemyType.FLOAT.value:
                    return 0.0
                case SQLAlchemyType.STRING.value:
                    return ""
                case SQLAlchemyType.DATETIME.value:
                    return datetime.now()
                case SQLAlchemyType.NUMERIC.value:
                    return Decimal("0.00")
                case _:
                    return None
        if type_ == SQLAlchemyType.DATETIME.value and isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError as e:
                raise ValueError(
                    f"Invalid datetime format for key '{key}': {value}"
                ) from e
        if type_ == SQLAlchemyType.NUMERIC.value and isinstance(value, str):
            try:
                return Decimal(value)
            except ValueError as e:
                raise ValueError(
                    f"Invalid decimal format for key '{key}': {value}"
                ) from e
        return value
