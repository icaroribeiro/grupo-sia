from typing import Union
from beanie import Document
from langchain_core.tools import BaseTool
from pymongo.errors import DuplicateKeyError

from src.layers.core_logic_layer.logging import logger


class InsertToMongoDBTool(BaseTool):
    name: str = "insert_to_mongodb_tool"
    description: str = """
    Insert documents into MongoDB collections using Beanie ODM.
    
    Args:
        documents_map (dict[str, list[Document]]): Map of Beanie document classes.
    
    Returns:
        Union[str, int | None]: Status message indicating success, warning or failure
        along with the number of inserted documents.
    """

    async def _arun(
        self, documents_map: dict[str, list[Document]]
    ) -> Union[str, int | None]:
        logger.info("Started inserting documents from map into MongoDB...")
        count_map: dict[str, int] = dict()
        if len(documents_map) > 0:
            for document_class_name, document_classes in documents_map.items():
                if count_map.get(document_class_name, None) is None:
                    count_map[document_class_name] = 0
                for document_class in document_classes:
                    try:
                        await document_class.insert()
                        count_map[document_class_name] += 1
                    except DuplicateKeyError:
                        message = "Warning: Document already exists. "
                        f"Skipping duplicate document: {document_class.model_dump_json()}"
                        logger.warning(message)
                        continue
                    except Exception as error:
                        message = f"Error: Failed to insert document {document_class} into MongoDB: {error}"
                        logger.error(message)
                        return (message, None)

        if len(count_map) > 0:
            total_count: int = 0
            for document_class_name, count in count_map.items():
                message = (
                    f"Success: {count} document(s) inserted into {document_class_name} "
                    "collection"
                )
                logger.info(message)
            message = (
                f"Success: Total of {total_count} document(s) inserted into MongoDB"
            )
            return (message, total_count)
        else:
            message = "Warning: No documents to insert into MongoDB."
            logger.warning(message)
            return (message, 0)

    def _run(self, *args, **kwargs) -> str:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
