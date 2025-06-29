import asyncio
import os
import re
from typing import Dict, Generic, TypeVar
from src.layers.core_logic_layer.logging import logger
from crewai.tools import BaseTool
import pandas as pd
from src.layers.data_access_layer.mongodb.repositories.base_repository import (
    BaseRepository,
)
from abc import ABC

from src.layers.data_access_layer.mongodb.repositories.invoice_repository import (
    InvoiceRepository,
)
from src.layers.data_access_layer.mongodb.repositories.invoice_item_repository import (
    InvoiceItemRepository,
)

RepositoryType = TypeVar("Repository", bound=BaseRepository)


class BaseInsertMongoTool(BaseTool, ABC, Generic[RepositoryType]):
    repository: RepositoryType
    columns_to_rename: Dict[str, str]
    csv_file_suffix: str

    def __init__(
        self,
        repository: RepositoryType,
        columns_to_rename: Dict[str, str],
        csv_file_suffix: str,
    ):
        super().__init__()
        self.repository = repository
        self.columns_to_rename = columns_to_rename
        self.csv_file_suffix = csv_file_suffix

    def _run(self, csv_paths: list) -> str:
        results = []

        for csv_path in csv_paths:
            csv_name = os.path.basename(csv_path)

            if not re.match(rf"\d{{6}}_{self.csv_file_prefix}\.csv$", csv_name):
                results.append(
                    f"For {csv_name}: Skipped (does not match {self.csv_file_prefix}.csv pattern)."
                )
                continue

            try:
                df = pd.read_csv(csv_path)
                data = df.rename(columns=self.columns_to_rename).to_dict("records")
                result = asyncio.run(self.repository.insert_many(data))
                results.append(f"For {csv_name}: {result}")
            except Exception as err:
                err = f"Error processing {csv_name}: {err}"
                logger.error(err)
                results.append()
            return "\n".join(results)


class InvoiceInsertMongoTool(BaseInsertMongoTool[InvoiceRepository]):
    name: str = "Invoice Insert Mongo Tool"
    description: str = """
        Inserts data from CSV files with suffix YYYYMM_NFe_NotaFiscal.csv into MongoDB for InvoiceDocument.
    """

    def __init__(self, repository: InvoiceRepository):
        super().__init__(
            repository=repository,
            columns_to_rename={
                "CHAVE DE ACESSO": "access_key",
            },
            csv_file_suffix="NFe_NotaFiscal",
        )


class InvoiceItemInsertMongoTool(BaseInsertMongoTool[InvoiceItemRepository]):
    name: str = "Invoice Item Insert Mongo Tool"
    description: str = """
        Inserts data from CSV files with suffix YYYYMM_NFe_NotaFiscalItem.csv into MongoDB for InvoiceItemDocument.
    """

    def __init__(self, repository: InvoiceItemRepository):
        super().__init__(
            repository=repository,
            columns_to_rename={
                "CHAVE DE ACESSO": "access_key",
            },
            csv_file_suffx="NFe_NotaFiscalItem",
        )


class InsertMongoTool(BaseTool):
    name: str = "Insert Mongo Tool"
    description: str = """
        Inserts data from multiple CSV files into MongoDB using specialized insert tools.
        
        Arguments:
            csv_paths (list): The CSV file paths.
    """

    def __init__(self, tools: list[BaseInsertMongoTool]):
        super().__init__()
        self.tools = tools

    def _run(self, csv_paths: list) -> str:
        results = []

        for csv_path in csv_paths:
            csv_results = [f"Insertion for {os.path.basename(csv_path)}:"]
            for tool in self.tools:
                result = tool._run(csv_path=csv_path)
                csv_results.append(result)
            results.append("\n".join(csv_results))

        return "\n".join(results)
