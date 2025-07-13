import os
import re
from typing import Dict, Union

from beanie import Document
from langchain_core.tools import BaseTool

from src.layers.business_layer.ai_agents.models.invoice_ingestion_args import (
    InvoiceIngestionArgs,
)
from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_args import (
    InvoiceItemIngestionArgs,
)
from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.mongodb.documents.invoice_document import (
    InvoiceDocument,
)
from src.layers.data_access_layer.mongodb.documents.invoice_item_document import (
    InvoiceItemDocument,
)


class MapCSVToIngestionArgsTool(BaseTool):
    name: str = "map_csv_to_ingestion_args"
    description: str = """
    Map CSV files to ingestion arguments used to insert documents into MongoDB.
    
    Args:
        file_paths (list[str]): List of paths to the CSV files.
    
    Returns:
        Union[str, dict[str, Union[list[InvoiceIngestionArgs], list[InvoiceItemIngestionArgs]]]
        | None]: Status message indicating success or failure along with the dictionary 
        of lists of ingestion arguments on success or 'None' on failure.
    """

    def _run(
        self, file_paths: list[str]
    ) -> Union[
        str,
        dict[str, Union[list[InvoiceIngestionArgs], list[InvoiceItemIngestionArgs]]]
        | None,
    ]:
        logger.info("Started mapping CSV files to ingestion arguments...")
        suffix_to_args: dict[
            str, Union[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
        ] = {
            "NFe_NotaFiscal": InvoiceIngestionArgs,
            "NFe_NotaFiscalItem": InvoiceItemIngestionArgs,
        }
        ingestion_args_map: Dict[
            str, Union[list[InvoiceIngestionArgs], list[InvoiceItemIngestionArgs]]
        ] = dict()
        try:
            for file_path in file_paths:
                matched = False
                file_name = os.path.basename(file_path)
                for suffix, args_class in suffix_to_args.items():
                    if ingestion_args_map.get(suffix, None) is None:
                        ingestion_args_map[suffix] = list()

                    if re.match(rf"\d{{6}}_{suffix}\.csv$", file_name):
                        document_class: Document
                        match suffix:
                            case "NFe_NotaFiscal":
                                document_class = InvoiceDocument
                                matched = True
                            case "NFe_NotaFiscalItem":
                                document_class = InvoiceItemDocument
                                matched = True
                            case _:
                                continue
                        ingestion_args_map[suffix].append(
                            args_class(
                                file_path=file_path, document_class=document_class
                            )
                        )
                        break
                if not matched:
                    message = (
                        f"Warning: File {file_name} does not match expected format "
                        "(YYYYMM_NFe_NotaFiscal.csv or YYYYMM_NFe_NotaFiscalItem.csv)"
                    )
                    logger.warning(message)
            message = f"Success: Files {file_paths} mapped to ingestion arguments"
            logger.info(message)
            return (message, ingestion_args_map)
        except Exception as error:
            message = f"Error: Failed to map CSV files to ingestion arguments: {error}"
            logger.error(message)
            return (message, None)
