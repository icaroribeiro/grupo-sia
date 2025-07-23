from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.layers.data_access_layer.postgresdb.models.base_model import BaseModel


class Consumer(BaseModel):
    __tablename__ = "consumer"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        name="name",
    )
    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        name="age",
    )
