# from typing import Type

# import pandas as pd
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
# from src.layers.data_access_layer.postgresdb.models.invoice_model import InvoiceModel


# class MapIngestionArgsToDBModelsInput(BaseModel):
#     """Input schema for MapIngestionArgsToDBModelsTool."""

#     ingestion_args_dict: dict[
#         int, list[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
#     ] = Field(..., description="A dictionary of ingestion arguments.")


# class MapIngestionArgsToDBModelsTool(BaseTool):
#     name: str = "map_ingestion_args_to_db_models_tool"
#     description: str = """
#     Map a dictionary of ingestion arguments to a dictionary of SQLALchemy database models.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (dictionary with integer keys and lists of SQLAlchemy database models on success or None on failure.)
#     """
#     args_schema: Type[BaseModel] = MapIngestionArgsToDBModelsInput

#     def _run(
#         self,
#         ingestion_args_dict: dict[
#             int, list[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
#         ],
#     ) -> ToolOutput:
#         logger.info("The MapIngestionArgsToDBModelsTool call has started...")
#         models_dict: dict[int, list[InvoiceModel | InvoiceItemModel]] = dict()
#         for key, ingestion_args_list in ingestion_args_dict.items():
#             if models_dict.get(key) is None:
#                 models_dict[key] = list()

#             for ingestion_args in ingestion_args_list:
#                 file_path = ingestion_args.file_path
#                 model_class: InvoiceModel | InvoiceItemModel = (
#                     ingestion_args.model_class
#                 )
#                 df: pd.DataFrame
#                 try:
#                     df = pd.read_csv(
#                         file_path,
#                         encoding="latin1",
#                         sep=";",
#                         dtype=model_class.get_csv_columns_to_dtypes(),
#                     )
#                 except FileNotFoundError as error:
#                     message = f"Error: Failed to find file at {file_path}: {error}"
#                     logger.error(message)
#                     return ToolOutput(messsage=message, cotent=None)
#                 except UnicodeDecodeError as error:
#                     message = (
#                         f"Error: Failed to decode data from file {file_path}: {error}"
#                     )
#                     logger.error(message)
#                     return ToolOutput(message=message, result=None)
#                 except Exception as error:
#                     message = f"Error: Failed to read file {file_path}: {error}"
#                     logger.error(message)
#                     return ToolOutput(message=message, result=None)

#                 try:
#                     for index, row in df.iterrows():
#                         try:
#                             model_data = {}
#                             for (
#                                 csv_col,
#                                 doc_field_info,
#                             ) in model_class.get_csv_columns_to_model_fields().items():
#                                 field_name = doc_field_info["field"]
#                                 converter = doc_field_info.get("converter")
#                                 value = row.get(csv_col)
#                                 if value is pd.NA or pd.isna(value):
#                                     value = None

#                                 if converter:
#                                     try:
#                                         value = converter(value)
#                                     except ValueError as error:
#                                         message = f"Warning: Could not convert '{value}' for field '{field_name}' in row {index + 1} of {file_path}: {error}"
#                                         logger.warning(message)
#                                         continue
#                                 model_data[field_name] = value
#                             model = model_class(**model_data)
#                             models_dict[key].append(model)
#                         except Exception as error:
#                             message = f"Error: Failed to process row {index + 1} from {file_path}: {error}"
#                             logger.error(message)
#                             continue
#                     message = f"Success: Models mapped from file {file_path}"
#                 except Exception as error:
#                     message = f"Error: Failed to map ingestion arguments dict {ingestion_args_dict} to models dict: {error}"
#                     logger.error(message)
#                     return ToolOutput(message=message, result=None)
#         logger.info("The MapIngestionArgsToDBModelsTool call has finished.")
#         return ToolOutput(message=message, result=models_dict)

#     async def _arun(
#         self,
#         ingestion_args_dict: dict[
#             int, list[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
#         ],
#     ) -> ToolOutput:
#         return self._run(ingestion_args_dict=ingestion_args_dict)
