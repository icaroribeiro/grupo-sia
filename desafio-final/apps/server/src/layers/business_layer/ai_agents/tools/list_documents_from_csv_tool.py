from typing import Union

import pandas as pd
from beanie import Document
from langchain_core.tools import BaseTool

from src.layers.core_logic_layer.logging import logger


class ListDocumentsFromCSVTool(BaseTool):
    name: str = "list_documents_from_csv_tool"
    description: str = """
    List Beanie document classes generated from a CSV file.

    Args:
        file_path (str): Path to the CSV file.
        document_class (Document): Beanie document class.
    
    Returns:
        Union[str, list[Document] | None]: Status message indicating success, warning or 
        failure along with list of Beanie document classes on success or 'None' on failure.
    """

    def _run(
        self,
        file_path: str,
        document_class: Document,
    ) -> Union[str, list[Document] | None]:
        logger.info("Started listing Beanie document classes...")
        try:
            df = pd.read_csv(
                file_path,
                encoding="latin1",
                sep=";",
                dtype=document_class.get_csv_columns_to_dtypes(),
            )
        except FileNotFoundError as error:
            message = f"Error: Failed to find file at {file_path}: {error}"
            logger.error(message)
            return (message, None)
        except UnicodeDecodeError as error:
            message = f"Error: Failed to decode data from file {file_path}: {error}"
            logger.error(message)
            return (message, None)
        except Exception as error:
            message = f"Error: Failed to read file {file_path}: {error}"
            logger.error(message)
            return (message, None)

        document_classes: list[Document] = list()
        try:
            for index, row in df.iterrows():
                try:
                    doc_data = {}
                    for (
                        csv_col,
                        doc_field_info,
                    ) in document_class.get_csv_columns_to_document_fields().items():
                        field_name = doc_field_info["field"]
                        converter = doc_field_info.get("converter")
                        value = row.get(csv_col)
                        if value is pd.NA or pd.isna(value):
                            value = None

                        if converter:
                            try:
                                value = converter(value)
                            except ValueError as error:
                                message = f"Warning: Could not convert '{value}' for field '{field_name}' in row {index + 1} of {file_path}: {error}"
                                logger.warning(message)
                                continue
                        doc_data[field_name] = value
                    doc = document_class(**doc_data)
                    document_classes.append(doc)
                except Exception as error:
                    message = f"Error: Failed to process row {index + 1} from {file_path}: {error}"
                    logger.error(message)
                    continue
            message = f"Success: Documents listed from file {file_path}"
            return (message, document_classes)
        except Exception as error:
            message = f"Error: Failed to list documents from {file_path}: {error}"
            logger.error(message)
            return (message, None)
