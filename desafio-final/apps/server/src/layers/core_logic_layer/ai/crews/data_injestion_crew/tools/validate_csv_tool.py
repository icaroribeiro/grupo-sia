import os
import re

from crewai.tools import BaseTool
import pandas as pd

from abc import ABC
from src.layers.core_logic_layer.logging import logger


class BaseValidateCSVTool(BaseTool, ABC):
    expected_columns: set[str]
    document_name: str
    csv_file_suffix: str

    def __init__(
        self, expected_columns: set[str], document_name: str, csv_file_suffix: str
    ):
        super().__init__()
        self.expected_columns = expected_columns
        self.document_name = document_name
        self.csv_file_suffix = csv_file_suffix

    def _run(self, csv_path: str) -> str:
        csv_name = os.path.basename(csv_path)

        if not re.match(rf"\d{{6}}_{self.csv_file_suffix}\.csv$", csv_name):
            return f"  {self.document_name}: Skipped {csv_name} (does not match {self.csv_file_suffix}.csv pattern)."

        try:
            df = pd.read_csv(csv_path)
            csv_columns = set(df.columns)
            if self.expected_columns.issubset(csv_columns):
                return f"  {self.document_name}: All required columns {self.expected_columns} found in {csv_name}."
            else:
                missing = self.expected_columns - csv_columns
                return (
                    f"  {self.document_name}: Missing columns {missing} in {csv_name}."
                )
        except Exception as err:
            err = f"  {self.document_name}: Error validating {csv_name}: {err}"
            logger.error(err)
            return err


class InvoiceValidateCSVTool(BaseValidateCSVTool):
    name: str = "Invoice Validate CSV Tool"
    description: str = """
        Validates CSV files with pattern YYYYMM_NFe_NotaFiscal.csv against InvoiceDocument fields.
    """

    def __init__(self):
        super().__init__(
            expected_columns={"CHAVE DE ACESSO"},
            document_name="InvoiceDocument",
            csv_file_suffix="NFe_NotaFiscal",
        )


class InvoiceItemValidateCSVTool(BaseValidateCSVTool):
    name: str = "Invoice Item Validate CSV Tool"
    description: str = """
        Validates CSV files with pattern YYYYMM_NFe_NotaFiscalItem.csv against InvoiceItemDocument fields.
    """

    def __init__(self):
        super().__init__(
            expected_columns={"CHAVE DE ACESSO"},
            document_name="InvoiceItemDocument",
            csv_file_suffix="NFe_NotaFiscalItem",
        )


class ValidateCSVTool(BaseTool):
    name: str = "Validate CSV Tool"
    description: str = """
        Validates multiple CSV files against specific Beanie document fields using specialized tools.

        Arguments:
            csv_paths (list): The CSV file paths.
    """

    def __init__(self, tools: list[BaseValidateCSVTool]):
        super().__init__()
        self.tools = tools

    def _run(self, csv_paths: list) -> str:
        results = []

        for csv_path in csv_paths:
            csv_results = [f"Validation for {os.path.basename(csv_path)}:"]
            for tool in self.tools:
                result = tool._run(csv_path=csv_path)
                csv_results.append(result)
            results.append("\n".join(csv_results))

        return "\n".join(results)
