from beanie import Document
from typing import Generic, TypeVar
from abc import ABC
from src.layers.core_logic_layer.logging import logger

DocumentType = TypeVar("DocumentType", bound=Document)


class BaseRepository(ABC, Generic[DocumentType]):
    def __init__(self, document: DocumentType):
        self.document = document

    async def insert_many_from_csv_data(self, csv_data: list[dict]) -> str:
        try:
            documents = [self.document(**item) for item in csv_data]
            await self.document.insert_many(documents)
            return f"Inserted {len(documents)} {self.document.__name__} documents."
        except Exception as err:
            logger.error(f"Error inserting {self.document.__name__} documents: {err}")
            return err
