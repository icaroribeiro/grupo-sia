import os
import re
import uuid
import zipfile
from typing import Annotated, Any, Sequence, Type, TypedDict
import pandas as pd
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from src.layers.business_layer.ai_agents.models.invoice_item_model import (
    InvoiceItemModel,
)
from src.layers.business_layer.ai_agents.models.invoice_model import InvoiceModel
from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
    InvoiceItemModel as SQLAlchemyInvoiceItemModel,
)
from src.layers.data_access_layer.postgresdb.models.invoice_model import (
    InvoiceModel as SQLAlchemyInvoiceModel,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


# --- Pydantic model definitions with the fix ---
class InvoiceIngestionArgs(BaseModel):
    table_name: str = Field(default="invoice", description="Database table name.")
    model: InvoiceModel = Field(..., description="Pydantic InvoiceModel class.")


class InvoiceItemIngestionArgs(BaseModel):
    table_name: str = Field(default="invoice_item", description="Database table name.")
    model: InvoiceItemModel = Field(..., description="Pydantic InvoiceItemModel class.")


class ToolOutput(BaseModel):
    message: str = ""
    result: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str
    tool_output: ToolOutput


class UnzipFilesFromZipArchiveInput(BaseModel):
    """Input schema for UnzipFilesFromZipArchiveTool."""

    file_path: str = Field(..., description="Path to the ZIP file.")
    destination_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )


class UnzipFilesFromZipArchiveTool(BaseTool):
    name: str = "unzip_files_from_zip_archive_tool"
    description: str = """
    Unzip files from ZIP archive to a destination directory.
    Returns:
        ToolOutput: An object containing a status message indicating success, warning or failure
        (string) and result (list of paths of extracted files from ZIP archive on success or empty list on failure).
    """
    args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

    def _run(self, file_path: str, destination_dir_path: str) -> ToolOutput:
        logger.info("The UnzipFilesFromZipArchiveTool call has started...")
        try:
            # Ensure the destination directory exists
            os.makedirs(destination_dir_path, exist_ok=True)

            # List to store extracted file paths
            extracted_files = []

            # Unzip the file
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(destination_dir_path)
                # Get the list of extracted files
                extracted_files = [
                    os.path.join(destination_dir_path, name)
                    for name in zip_ref.namelist()
                    if not name.endswith("/")
                ]

            # Normalize file paths to use forward slashes
            extracted_files = [file.replace("\\", "/") for file in extracted_files]

            message = f"Success: ZIP file {file_path} extracted"
            logger.info(f"{message}: {','.join(extracted_files)}")
            logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
            return ToolOutput(message=message, result=extracted_files)

        except Exception as e:
            message = f"Error unzipping file {file_path}: {str(e)}"
            logger.error(message)
            logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
            return ToolOutput(message=message, result=[])

    async def _arun(self, file_path: str, destination_dir_path: str) -> ToolOutput:
        return self._run(file_path=file_path, destination_dir_path=destination_dir_path)


class MapCSVsToIngestionArgsInput(BaseModel):
    """Input schema for MapCSVsToIngestionArgsTool."""

    file_paths: list[str] = Field(
        ..., description="List of paths of extracted CSV files."
    )


class MapCSVsToIngestionArgsTool(BaseTool):
    name: str = "map_csvs_to_ingestion_args_tool"
    description: str = """
    Map a list of paths of extracted CSV files to a dictionary of lists of ingestion arguments.
    Returns:
        ToolOutput: An object containing a status message indicating success, warning or failure
        (string) and result (dictionary with integer keys and lists of ingestion arguments on success or None on failure.)
    """
    args_schema: Type[BaseModel] = MapCSVsToIngestionArgsInput

    def _run(self, file_paths: list[str]) -> ToolOutput:
        logger.info("The MapCSVsToIngestionArgsTool call has started...")
        suffix_to_args: dict[
            tuple[int, str],
            tuple[
                InvoiceIngestionArgs | InvoiceItemIngestionArgs,
                InvoiceModel | InvoiceItemModel,
            ],
        ] = {
            (0, "NFe_NotaFiscal"): (InvoiceIngestionArgs, InvoiceModel),
            (1, "NFe_NotaFiscalItem"): (InvoiceItemIngestionArgs, InvoiceItemModel),
        }
        ingestion_args_dict: dict[
            int, list[InvoiceIngestionArgs | InvoiceItemIngestionArgs]
        ] = dict()

        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            for (key, suffix), (args_class, model_class) in suffix_to_args.items():
                if ingestion_args_dict.get(key) is None:
                    ingestion_args_dict[key] = []

                if re.match(rf"\d{{6}}_{suffix}\.csv$", file_name):
                    try:
                        df = pd.read_csv(
                            file_path,
                            encoding="latin1",
                            sep=";",
                            dtype=model_class.get_csv_columns_to_dtypes()
                            if hasattr(model_class, "get_csv_columns_to_dtypes")
                            else str,
                        )
                    except FileNotFoundError as error:
                        message = f"Error: Failed to find file at {file_path}: {error}"
                        logger.error(message)
                        return ToolOutput(message=message, result=None)
                    except UnicodeDecodeError as error:
                        message = f"Error: Failed to decode data from file {file_path}: {error}"
                        logger.error(message)
                        return ToolOutput(message=message, result=None)
                    except Exception as error:
                        message = f"Error: Failed to read file {file_path}: {error}"
                        logger.error(message)
                        return ToolOutput(message=message, result=None)

                    try:
                        for index, row in df.iterrows():
                            try:
                                model_data = {}
                                for (
                                    csv_col,
                                    doc_field_info,
                                ) in model_class.get_csv_columns_to_model_fields().items():
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
                                    model_data[field_name] = value
                                model = model_class(**model_data)
                                ingestion_args_dict[key].append(args_class(model=model))
                            except Exception as error:
                                message = f"Error: Failed to process row {index + 1} from {file_path}: {error}"
                                logger.error(message)
                                continue
                        message = f"Success: Models mapped from file {file_path}"
                    except Exception as error:
                        message = f"Error: Failed to map ingestion arguments dict {ingestion_args_dict} to models dict: {error}"
                        logger.error(message)
                        return ToolOutput(message=message, result=None)

        serialized_models_dict = {
            key: [
                {
                    "table_name": ingestion_arg.table_name,
                    "model": ingestion_arg.model.model_dump(),
                }
                for ingestion_arg in ingestion_args
            ]
            for key, ingestion_args in ingestion_args_dict.items()
        }

        logger.info("The MapCSVsToPydanticModelsTool call has finished.")
        return ToolOutput(message=message, result=serialized_models_dict)

    async def _arun(self, file_paths: list[str]) -> ToolOutput:
        return self._run(file_paths=file_paths)


class InsertRecordsIntoDatabaseInput(BaseModel):
    """Input schema for InsertRecordsIntoDatabaseTool."""

    ingestion_args_dict: dict[
        int, list[InvoiceIngestionArgs | InvoiceItemIngestionArgs]
    ] = Field(..., description="A dictionary of lists of ingestion arguments.")


class InsertRecordsIntoDatabaseTool(BaseTool):
    name: str = "insert_records_into_database_tool"
    description: str = """
    Insert SQLAlchemy database models into Postgres database.
    Returns:
        ToolOutput: An object containing a status message indicating success, warning or failure
        (string) and result (total number of inserted records on success or None on failure).
    """
    postgresdb: PostgresDB
    args_schema: Type[BaseModel] = InsertRecordsIntoDatabaseInput

    def __init__(self, postgresdb: PostgresDB):
        super().__init__(postgresdb=postgresdb)
        self.postgresdb = postgresdb

    async def _arun(
        self,
        ingestion_args_dict: dict[int, list[dict[str, Any]]],
    ) -> ToolOutput:
        logger.info("The InsertRecordsIntoDatabaseTool call has started...")
        sqlalchemy_models_dict: dict[
            int, list[SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel]
        ] = dict()

        for key, ingestion_args_list in ingestion_args_dict.items():
            if sqlalchemy_models_dict.get(key) is None:
                sqlalchemy_models_dict[key] = []

            for ingestion_args in ingestion_args_list:
                table_name = ingestion_args["table_name"]
                model_class: Type[SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel]
                # Replace match with if-elif
                if table_name == SQLAlchemyInvoiceModel.get_table_name():
                    model_class = SQLAlchemyInvoiceModel
                elif table_name == SQLAlchemyInvoiceItemModel.get_table_name():
                    model_class = SQLAlchemyInvoiceItemModel
                else:
                    message = f"Error: Invalid table name {table_name}"
                    logger.error(message)
                    return ToolOutput(message=message, result=None)

                try:
                    model = model_class.from_data(data=ingestion_args["model"])
                    sqlalchemy_models_dict[key].append(model)
                except Exception as error:
                    message = f"Error: Failed to create SQLAlchemy model from args {ingestion_args}: {error}"
                    logger.error(message)
                    continue

        count_map: dict[str, int] = dict()
        try:
            async with self.postgresdb.async_session() as async_session:
                if len(sqlalchemy_models_dict) > 0:
                    for _, models in sorted(sqlalchemy_models_dict.items()):
                        for model in models:
                            if count_map.get(model.get_table_name(), None) is None:
                                count_map[model.get_table_name()] = 0
                            try:
                                async_session.add(model)
                                count_map[model.get_table_name()] += 1
                            except IntegrityError:
                                message = f"Warning: Model already exists. Skipping duplicate model: {getattr(model, 'access_key', 'N/A')}"
                                logger.warning(message)
                                continue
                            except Exception as error:
                                await async_session.rollback()
                                message = (
                                    f"Error: Failed to insert model {model}: {error}"
                                )
                                logger.error(message)
                                return ToolOutput(message=message, result=None)
                        try:
                            await async_session.commit()
                            message = f"Success: All {model.get_table_name()} table records have been committed."
                            logger.info(message)
                        except Exception as error:
                            await async_session.rollback()
                            message = f"Error: Failed to commit the current transaction: {error}"
                            logger.error(message)
                            return ToolOutput(message=message, result=None)
        except Exception as error:
            message = f"Error: Failed to establish database connection: {error}"
            logger.error(message)
            return ToolOutput(message=message, result=None)

        if len(count_map) > 0:
            total_count: int = 0
            for model_name, count in count_map.items():
                total_count += count
                message = f"Success: {count} record(s) inserted into {model_name} table"
                logger.info(message)
            message = f"Success: Total of {total_count} record(s) inserted into Postgres database"
            logger.info("The InsertRecordsIntoDatabaseTool call has finished.")
            return ToolOutput(message=message, result=total_count)
        else:
            message = "Warning: No records to insert into Postgres database."
            logger.warning(message)
            return ToolOutput(message=message, result=0)

    def _run(
        self,
        ingestion_args_dict: dict[int, list[dict]],
    ) -> ToolOutput:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)


class DataIngestionWorkflow:
    def __init__(
        self,
        llm: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_records_into_database_tool: InsertRecordsIntoDatabaseTool,
    ):
        self.__name = "data_ingestion_workflow"
        self.llm = llm

        self.unzip_tool = unzip_files_from_zip_archive_tool
        self.map_csvs_tool = map_csvs_to_ingestion_args_tool
        self.insert_database_tool = insert_records_into_database_tool
        self.worker_1_tools = [self.unzip_tool]
        self.worker_2_tools = [self.map_csvs_tool]
        self.worker_3_tools = [self.insert_database_tool]
        self.all_tools = self.worker_1_tools + self.worker_2_tools + self.worker_3_tools

        self.__graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(state_schema=WorkflowState)

        # --- 1. Define the Supervisor Node (Router) - UNCHANGED ---
        def call_supervisor(state: WorkflowState):
            print("---SUPERVISOR---")
            messages = state["messages"]
            worker_names = ["worker_node_1", "worker_node_2", "worker_node_3"]
            worker_names_str = ", ".join(worker_names)
            finish_node = '{{"next": "FINISH"}}'
            entry_node = (
                f'{{{{"next": "{worker_names[0]}"}}}}'
                if worker_names
                else '{{"next": "FINISH"}}'
            )
            next_node = '{{"next": "<next_node>"}}'
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a supervisor routing tasks to workers. Based on the conversation history, decide the next step.
                        Current available workers: [{worker_names_str}].
                        Analyze the user request and conversation history to determine 
                        which worker can handle it best.
                        
                        If the input messages indicate that the task is complete, or if 
                        the state contains 'next': 'FINISH', return {finish_node}.
                        
                        Respond in the following JSON format:
                        ```json
                        {next_node}
                        ```
                        where <next_node> is the node to route to (e.g., {entry_node} 
                        or {finish_node}).
                        """.format(
                            worker_names_str=worker_names_str,
                            finish_node=finish_node,
                            next_node=next_node,
                            entry_node=entry_node,
                        ),
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            ).partial(
                worker_names_str=", ".join(worker_names_str),
                finish_node=finish_node,
                next_node=next_node,
                entry_node=entry_node,
            )
            chain = prompt | self.llm | JsonOutputParser()
            response = chain.invoke({"messages": messages})
            print(f"Supervisor routing to: {response['next']}")
            return {"messages": messages, "next": response["next"]}

        # --- 2. Define Worker Node 1 (Unzip Task) - UNCHANGED ---
        def call_worker_node_1(state: WorkflowState):
            print("---WORKER NODE 1 (UNZIP AGENT)---")
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an unzip specialist. You have access to a tool to unzip files. Call this tool to start the workflow.",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            llm_with_tools = self.llm.bind_tools(self.worker_1_tools)
            chain = prompt | llm_with_tools
            response = chain.invoke({"messages": state["messages"]})
            if hasattr(response, "tool_calls") and response.tool_calls:
                seen = set()
                unique_tool_calls = []
                for tool_call in response.tool_calls:
                    tool_key = (tool_call["name"], str(tool_call["args"]))
                    if tool_key not in seen:
                        seen.add(tool_key)
                        unique_tool_calls.append(tool_call)
                response.tool_calls = unique_tool_calls

            return {
                "messages": state["messages"] + [response],
                "next": "tools"
                if hasattr(response, "tool_calls") and response.tool_calls
                else "supervisor",
                "tool_output": state.get("tool_output", ToolOutput()),
            }

        # --- 3. Define Worker Node 2 (Mapping Tasks) - MODIFIED ---
        def call_worker_node_2(state: WorkflowState):
            print("---WORKER NODE 2 (MAPPING AGENT)---")
            # CHANGE START: Escaped curly braces and moved partial to invoke
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a data mapping specialist. A previous tool call has unzipped files. Your task is to use the 'map_csvs_to_ingestion_args_tool' with the unzipped file paths from the tool output to map the data to ingestion arguments. The unzipped file paths are available in the 'result' attribute of the tool output from the state: {tool_output_result}. "
                        "Ensure your tool call uses 'file_paths' as the argument name, like so: 'map_csvs_to_ingestion_args_tool(file_paths={{...}})'.",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            llm_with_tools = self.llm.bind_tools(self.worker_2_tools)
            chain = prompt | llm_with_tools
            response = chain.invoke(
                {
                    "messages": state["messages"],
                    "tool_output_result": str(
                        state.get("tool_output", ToolOutput()).result
                    ),
                }
            )
            # CHANGE END
            if hasattr(response, "tool_calls") and response.tool_calls:
                seen = set()
                unique_tool_calls = []
                for tool_call in response.tool_calls:
                    tool_key = (tool_call["name"], str(tool_call["args"]))
                    if tool_key not in seen:
                        seen.add(tool_key)
                        unique_tool_calls.append(tool_call)
                response.tool_calls = unique_tool_calls

            print(f"\n\ntool_output: {state.get('tool_output', ToolOutput())}")
            return {
                "messages": state["messages"] + [response],
                "next": "tools"
                if hasattr(response, "tool_calls") and response.tool_calls
                else "supervisor",
                "tool_output": state.get("tool_output", ToolOutput()),
            }

        # --- 4. Define Worker Node 3 (Inserting Task)
        def call_worker_node_3(state: WorkflowState):
            print("---WORKER NODE 3 (INSERTING AGENT)---")
            # CHANGE START: Escaped curly braces and moved partial to invoke
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a data insertion specialist. Use the 'insert_records_into_database_tool' with a dictionary of lists of ingestion arguments from the previous tool output. The dictionary is in the 'result' attribute of the tool output from the state: {tool_output_result}. "
                        "Ensure your tool call uses 'ingestion_args_dict' as the argument name, like so: 'insert_records_into_database_tool(ingestion_args_dict={{...}})'.",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            llm_with_tools = self.llm.bind_tools(self.worker_3_tools)
            chain = prompt | llm_with_tools
            response = chain.invoke(
                {
                    "messages": state["messages"],
                    "tool_output_result": str(
                        state.get("tool_output", ToolOutput()).result
                    ),
                }
            )
            # CHANGE END
            if hasattr(response, "tool_calls") and response.tool_calls:
                seen = set()
                unique_tool_calls = []
                for tool_call in response.tool_calls:
                    tool_key = (tool_call["name"], str(tool_call["args"]))
                    if tool_key not in seen:
                        seen.add(tool_key)
                        unique_tool_calls.append(tool_call)
                response.tool_calls = unique_tool_calls

            print(f"\n\ntool_output: {state.get('tool_output', ToolOutput())}")
            return {
                "messages": state["messages"] + [response],
                "next": "tools"
                if hasattr(response, "tool_calls") and response.tool_calls
                else "supervisor",
                "tool_output": state.get(
                    "tool_output", ToolOutput()
                ),  # Preserve tool output
            }

        # def _parse_tool_output_string(output_string: str) -> dict:
        #     """
        #     Parses a custom tool output string of the format 'message="..." result=[...]'
        #     and returns a dictionary. Used as fallback for string outputs.
        #     """
        #     parsed_dict = {}
        #     message_match = re.search(r"message='(.*?)'", output_string, re.DOTALL)
        #     if message_match:
        #         parsed_dict["message"] = message_match.group(1)

        #     result_match = re.search(
        #         r"result=({.*?}|\[.*?\]|None)", output_string, re.DOTALL
        #     )
        #     if result_match:
        #         try:
        #             parsed_dict["result"] = ast.literal_eval(result_match.group(1))
        #         except (ValueError, SyntaxError) as e:
        #             logger.error(f"Error parsing result literal from string: {e}")
        #             parsed_dict["result"] = None

        #     return parsed_dict

        # async def tool_executor_node(state: WorkflowState):
        #     print("---TOOL EXECUTOR---")
        #     last_message = state["messages"][-1]
        #     tool_messages_to_add = []

        #     # Default tool_output
        #     tool_output = state.get(
        #         "tool_output", ToolOutput(message="No tool call executed.", result=None)
        #     )

        #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        #         for tool_call in last_message.tool_calls:
        #             tool_name = tool_call["name"]
        #             tool_args = tool_call["args"]
        #             tool = next(
        #                 (t for t in self.all_tools if t.name == tool_name), None
        #             )
        #             if not tool:
        #                 logger.error(f"Tool {tool_name} not found")
        #                 tool_messages_to_add.append(
        #                     ToolMessage(
        #                         content=f"Error: Tool {tool_name} not found",
        #                         tool_call_id=tool_call["id"],
        #                     )
        #                 )
        #                 continue
        #             try:
        #                 result = await tool._arun(**tool_args)
        #                 if isinstance(result, ToolOutput):
        #                     tool_output = result
        #                 elif isinstance(result, dict):
        #                     tool_output = ToolOutput(
        #                         message=result.get("message", "Message not provided."),
        #                         result=result.get("result", None),
        #                     )
        #                 else:
        #                     parsed_dict = _parse_tool_output_string(str(result))
        #                     tool_output = ToolOutput(
        #                         message=parsed_dict.get(
        #                             "message", "Could not parse string output."
        #                         ),
        #                         result=parsed_dict.get("result", None),
        #                     )
        #                 tool_messages_to_add.append(
        #                     ToolMessage(
        #                         content=str(
        #                             tool_output
        #                         ),  # Serialize for message history
        #                         tool_call_id=tool_call["id"],
        #                     )
        #                 )
        #             except Exception as e:
        #                 logger.error(f"Error executing tool {tool_name}: {e}")
        #                 tool_output = ToolOutput(
        #                     message=f"Error executing tool {tool_name}: {str(e)}",
        #                     result=None,
        #                 )
        #                 tool_messages_to_add.append(
        #                     ToolMessage(
        #                         content=str(tool_output), tool_call_id=tool_call["id"]
        #                     )
        #                 )

        #     print(f" --> tool_output: {tool_output}")
        #     return {
        #         "messages": state["messages"] + tool_messages_to_add,
        #         "tool_output": tool_output,
        #     }

        # async def tool_executor_node(state: dict[str, Any]) -> dict[str, Any]:
        #     # ... (code before the try block) ...

        #     try:
        #         tool_outputs = await tool_executor.ainvoke({"messages": [last_message]})
        #         print(f" ******** tool_outputs: {tool_outputs}")

        #         # Check if there are messages to process
        #         if not tool_outputs["messages"]:
        #             tool_output = ToolOutput(
        #                 message="No output received from tool executor."
        #             )
        #         else:
        #             first_tool_message = tool_outputs["messages"][0]
        #             print(f" ******** first_tool_message: {first_tool_message}")

        #             if isinstance(first_tool_message, ToolMessage):
        #                 # Handle both success and error cases from the tool
        #                 if first_tool_message.status == "error":
        #                     tool_output = ToolOutput(
        #                         message=f"Tool execution failed: {first_tool_message.content}",
        #                         result=None,
        #                     )
        #                 else:
        #                     # Parse the content string manually
        #                     try:
        #                         # Use a regular expression to find the 'message' and 'result' parts
        #                         match = re.match(
        #                             r"message='(.*?)' result=(.*)",
        #                             first_tool_message.content,
        #                         )
        #                         if match:
        #                             message_part = match.group(1)
        #                             result_part = match.group(2)

        #                             # Safely evaluate the result part, which should be a list or dict
        #                             parsed_result = ast.literal_eval(result_part)

        #                             tool_output = ToolOutput(
        #                                 message=message_part,
        #                                 result=parsed_result,
        #                             )
        #                         else:
        #                             # Fallback if the regex doesn't match the expected format
        #                             tool_output = ToolOutput(
        #                                 message=first_tool_message.content
        #                             )
        #                     except (ValueError, SyntaxError) as e:
        #                         print(f"Error parsing tool output: {e}")
        #                         # Fallback if ast.literal_eval fails
        #                         tool_output = ToolOutput(
        #                             message=first_tool_message.content
        #                         )
        #             else:
        #                 # If the message is not a ToolMessage, just use its content.
        #                 tool_output = ToolOutput(
        #                     message=str(first_tool_message.content)
        #                 )

        #     except Exception as e:
        #         logger.error(f"Error executing tool: {e}")
        #         tool_output = ToolOutput(message=f"Error executing tool: {str(e)}")

        #     print(f" --> tool_output: {tool_output}")
        #     return {
        #         "messages": state["messages"] + tool_outputs["messages"],
        #         "tool_output": tool_output,
        #     }

        # async def tool_executor_node(state: dict[str, Any]) -> dict[str, Any]:
        #     """Execute tools using ToolNode and return updated state with ToolOutput."""
        #     print("---TOOL EXECUTOR---")
        #     tool_executor = ToolNode(self.all_tools)
        #     last_message = state["messages"][-1]
        #     tool_output = state.get(
        #         "tool_output", ToolOutput(message="No tool call executed.")
        #     )

        #     if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        #         print(f" --> tool_output: {tool_output}")
        #         return {"messages": state["messages"], "tool_output": tool_output}

        #     try:
        #         tool_outputs = await tool_executor.ainvoke({"messages": [last_message]})
        #         print(f" ******** tool_outputs: {tool_outputs}")
        #         # Extract the first tool output (assuming single tool call for simplicity)
        #         raw_output = (
        #             tool_outputs["messages"][0].content
        #             if tool_outputs["messages"]
        #             else "No output received."
        #         )

        #         # Convert to ToolOutput
        #         if isinstance(raw_output, ToolOutput):
        #             tool_output = raw_output
        #         elif isinstance(raw_output, dict):
        #             tool_output = ToolOutput(
        #                 message=raw_output.get("message", "Message not provided."),
        #                 result=raw_output.get("result"),
        #             )
        #         else:
        #             tool_output = ToolOutput(message=str(raw_output))

        #     except Exception as e:
        #         logger.error(f"Error executing tool: {e}")
        #         tool_output = ToolOutput(message=f"Error executing tool: {str(e)}")

        #     print(f" --> tool_output: {tool_output}")
        #     return {
        #         "messages": state["messages"] + tool_outputs["messages"],
        #         "tool_output": tool_output,
        #     }

        async def tool_executor_node(state: WorkflowState):
            print("---TOOL EXECUTOR---")
            last_message = state["messages"][-1]
            tool_messages_to_add = []

            # Default tool_output
            tool_output = state.get(
                "tool_output", ToolOutput(message="No tool call executed.", result=None)
            )

            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool = next(
                        (t for t in self.all_tools if t.name == tool_name), None
                    )
                    if not tool:
                        logger.error(f"Tool {tool_name} not found")
                        tool_messages_to_add.append(
                            ToolMessage(
                                content=f"Error: Tool {tool_name} not found",
                                tool_call_id=tool_call["id"],
                            )
                        )
                        continue
                    try:
                        result = await tool._arun(**tool_args)
                        if isinstance(result, ToolOutput):
                            tool_output = result

                        if isinstance(result, dict):
                            tool_output = ToolOutput(
                                message=result.get("message", "Message not provided."),
                                result=result.get("result", None),
                            )

                        tool_messages_to_add.append(
                            ToolMessage(
                                content=str(
                                    tool_output
                                ),  # Serialize for message history
                                tool_call_id=tool_call["id"],
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        tool_output = ToolOutput(
                            message=f"Error executing tool {tool_name}: {str(e)}",
                            result=None,
                        )
                        tool_messages_to_add.append(
                            ToolMessage(
                                content=str(tool_output), tool_call_id=tool_call["id"]
                            )
                        )

            print(f" --> tool_output: {tool_output}")
            return {
                "messages": state["messages"] + tool_messages_to_add,
                "tool_output": tool_output,
            }

        # 6. Build the Graph
        workflow.add_node("supervisor", call_supervisor)
        workflow.add_node("worker_node_1", call_worker_node_1)
        workflow.add_node("worker_node_2", call_worker_node_2)
        workflow.add_node("worker_node_3", call_worker_node_3)
        workflow.add_node("tools", tool_executor_node)

        workflow.set_entry_point("supervisor")

        # The supervisor's routing logic is now expanded
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state["next"],
            {
                "worker_node_1": "worker_node_1",
                "worker_node_2": "worker_node_2",
                "worker_node_3": "worker_node_3",
                "FINISH": END,
            },
        )

        # def call_tools(
        #     state: WorkflowState,
        #     routes_to: str,
        # ) -> str:
        #     last_message = state["messages"][-1]
        #     logger.info(f"Last message: {last_message}")
        #     return (
        #         "tools"
        #         if hasattr(last_message, "tool_calls") and last_message.tool_calls
        #         else routes_to
        #     )

        # Edges from workers to the tool executor
        workflow.add_edge("worker_node_1", "tools")
        workflow.add_edge("worker_node_2", "tools")
        workflow.add_edge("worker_node_3", "tools")
        # workflow.add_conditional_edges(
        #     "worker_node_1",
        #     path=functools.partial(call_tools, routes_to="supervisor"),
        #     path_map={
        #         "tools": "tools",
        #         "supervisor": "supervisor",
        #     },
        # )
        # workflow.add_conditional_edges(
        #     "worker_node_2",
        #     path=functools.partial(call_tools, routes_to="supervisor"),
        #     path_map={
        #         "tools": "tools",
        #         "supervisor": "supervisor",
        #     },
        # )
        # workflow.add_conditional_edges(
        #     "worker_node_3",
        #     path=functools.partial(call_tools, routes_to="supervisor"),
        #     path_map={
        #         "tools": "tools",
        #         "supervisor": "supervisor",
        #     },
        # )

        # After any tool is executed, always loop back to the supervisor
        workflow.add_edge("tools", "supervisor")

        # Compile the graph
        graph = workflow.compile(checkpointer=MemorySaver())
        print("✅ Graph with all worker nodes compiled successfully!")
        print(graph.get_graph(xray=True).draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    # The `run` method from the previous answer can be used here without changes.
    async def run(self, input_message: str) -> dict:
        print(f"🚀 Starting {self.__name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}
        result = await self.__graph.ainvoke(
            input_state,
            config={"configurable": {"thread_id": thread_id}},
        )
        print("\n✅ DataIngestionWorkflow Finished.")
        final_message = "Workflow complete."
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                final_message = msg.content
                break
        print(f"Final Result: {final_message}")
        return result
