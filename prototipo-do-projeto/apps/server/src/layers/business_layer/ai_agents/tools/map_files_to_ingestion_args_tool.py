import os
import re
from typing import Tuple

from langchain_core.tools import BaseTool

from src.layers.core_logic_layer.logging import logger

from pydantic import BaseModel, Field
from typing import Type
from src.layers.business_layer.ai_agents.models.invoice_ingestion_args import (
    InvoiceIngestionArgs,
)
from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_args import (
    InvoiceItemIngestionArgs,
)
from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import InvoiceModel


class MapFilesToIngestionArgsInput(BaseModel):
    """Input schema for MapFilesToIngestionArgsTool."""

    file_paths: list[str] = Field(..., description="Paths to the ZIP file.")


class MapFilesToIngestionArgsTool(BaseTool):
    name: str = "map_files_to_ingestion_args_tool"
    description: str = """
    Map CSV files to a dictionary of ingestion arguments.
    Returns:
        Tuple[str, dict[Tuple[int, str], list[InvoiceIngestionArgs | InvoiceItemIngestionArgs]] | None]:
        A string for status message indicating success or failure along with the map of 
        ingestion arguments on success or 'None' on failure.
    """
    args_schema: Type[BaseModel] = MapFilesToIngestionArgsInput

    def _run(
        self, file_paths: list[str]
    ) -> Tuple[
        str,
        dict[Tuple[int, str], list[InvoiceIngestionArgs | InvoiceItemIngestionArgs]]
        | None,
    ]:
        logger.info("The MapFilesToIngestionArgsTool call started initiating...")
        suffix_to_args: dict[
            Tuple[int, str], list[InvoiceIngestionArgs | InvoiceItemIngestionArgs]
        ] = {
            (0, "NFe_NotaFiscal"): InvoiceIngestionArgs,
            (1, "NFe_NotaFiscalItem"): InvoiceItemIngestionArgs,
        }
        ingestion_args_dict: dict[
            Tuple[int, str], list[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
        ] = dict()
        try:
            for file_path in file_paths:
                matched = False
                file_name = os.path.basename(file_path)
                for tuple_, args_class in suffix_to_args.items():
                    if re.match(rf"\d{{6}}_{tuple_[1]}\.csv$", file_name):
                        model_class: InvoiceModel | InvoiceItemModel
                        match tuple_[1]:
                            case "NFe_NotaFiscal":
                                model_class = InvoiceModel
                                matched = True
                            case "NFe_NotaFiscalItem":
                                model_class = InvoiceItemModel
                                matched = True
                            case _:
                                continue
                        ingestion_args_dict[tuple_[0]].append(
                            args_class(file_path=file_path, model_class=model_class)
                        )
                        break
                if not matched:
                    message = (
                        f"Warning: File {file_name} does not match expected format "
                        "(YYYYMM_NFe_NotaFiscal.csv or YYYYMM_NFe_NotaFiscalItem.csv)"
                    )
                    logger.warning(message)
            message = f"Success: Files {file_paths} mapped to ingestion arguments list"
            logger.info(message)
            return (message, ingestion_args_dict)
        except Exception as error:
            message = f"Error: Failed to map files to ingestion arguments list: {error}"
            logger.error(message)
            return (message, None)

    async def _arun(
        self, file_paths: list[str]
    ) -> Tuple[
        str,
        dict[Tuple[int, str], list[InvoiceIngestionArgs | InvoiceItemIngestionArgs]]
        | None,
    ]:
        return self._run(file_paths=file_paths)
