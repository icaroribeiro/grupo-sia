# import os
# import re
# from typing import Type
# from langchain_core.tools import BaseTool
# from pydantic import BaseModel, Field
# from src.layers.business_layer.ai_agents.models.invoice_ingestion_args import (
#     InvoiceIngestionArgs,
# )
# from src.layers.business_layer.ai_agents.models.invoice_item_ingestion_args import (
#     InvoiceItemIngestionArgs,
# )
# from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
# from src.layers.core_logic_layer.logging import logger
# from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
#     InvoiceItemModel,
# )
# from src.layers.data_access_layer.postgresdb.models.invoice_model import (
#     InvoiceModel,
# )


# class MapCSVsToIngestionArgsInput(BaseModel):
#     """Input schema for MapCSVsToIngestionArgsTool."""

#     file_paths: list[str] = Field(
#         ..., description="List of paths of extracted CSV files."
#     )


# class MapCSVsToIngestionArgsTool(BaseTool):
#     name: str = "map_csvs_to_ingestion_args_tool"
#     description: str = """
#     Map a list of paths of extracted CSV files to a dictionary of ingestion arguments.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning, or failure
#         and a result dictionary with integer keys and lists of ingestion arguments (as dictionaries).
#     """
#     args_schema: Type[BaseModel] = MapCSVsToIngestionArgsInput

#     def _run(self, file_paths: list[str]) -> ToolOutput:
#         logger.info("The MapCSVsToIngestionArgsTool call has started...")
#         suffix_to_args: dict[
#             tuple[int, str], Type[InvoiceIngestionArgs | InvoiceItemIngestionArgs]
#         ] = {
#             (0, "NFe_NotaFiscal"): InvoiceIngestionArgs,
#             (1, "NFe_NotaFiscalItem"): InvoiceItemIngestionArgs,
#         }
#         ingestion_args_dict: dict[int, list[dict]] = {}
#         try:
#             for file_path in file_paths:
#                 matched = False
#                 file_name = os.path.basename(file_path)
#                 for tuple_key, args_class in suffix_to_args.items():
#                     if ingestion_args_dict.get(tuple_key[0]) is None:
#                         ingestion_args_dict[tuple_key[0]] = []

#                     if re.match(rf"\d{{6}}_{tuple_key[1]}\.csv$", file_name):
#                         model_class: Type[InvoiceModel | InvoiceItemModel]
#                         if tuple_key[1] == "NFe_NotaFiscal":
#                             model_class = InvoiceModel
#                         elif tuple_key[1] == "NFe_NotaFiscalItem":
#                             model_class = InvoiceItemModel
#                         else:
#                             continue
#                         # Convert ingestion args to a JSON-serializable dict
#                         args_instance = args_class(
#                             file_path=file_path, model_class=model_class
#                         )
#                         args_dict = {
#                             "file_path": args_instance.file_path,
#                             "model_class": model_class.__name__,  # Use class name as string
#                         }
#                         ingestion_args_dict[tuple_key[0]].append(args_dict)
#                         matched = True
#                         break
#                 if not matched:
#                     message = (
#                         f"Warning: File {file_name} does not match expected format "
#                         "(YYYYMM_NFe_NotaFiscal.csv or YYYYMM_NFe_NotaFiscalItem.csv)"
#                     )
#                     logger.warning(message)
#             message = f"Success: Files {file_paths} mapped to ingestion arguments list"
#             logger.info(message)
#             logger.info("The MapCSVsToIngestionArgsTool call has finished.")
#             return ToolOutput(message=message, result=ingestion_args_dict)
#         except Exception as error:
#             message = f"Error: Failed to map files {file_paths} to ingestion arguments dict: {error}"
#             logger.error(message)
#             logger.info("The MapCSVsToIngestionArgsTool call has finished.")
#             return ToolOutput(message=message, result={})

#     async def _arun(self, file_paths: list[str]) -> ToolOutput:
#         return self._run(file_paths=file_paths)
