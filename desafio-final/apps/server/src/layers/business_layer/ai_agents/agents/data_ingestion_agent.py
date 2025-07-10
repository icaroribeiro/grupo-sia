import os
import re
from typing import Dict, Union

from beanie import Document
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI

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


class DataIngestionAgent(AgentExecutor):
    def __init__(self, llm: ChatGoogleGenerativeAI, tools: list[BaseTool]):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AI agent.""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
        super().__init__(agent=agent, tools=tools, verbose=True)

    @classmethod
    def map_csv_files_to_ingestion_args(
        cls,
        file_paths: list[str],
    ) -> Dict[str, Union[list[InvoiceIngestionArgs], list[InvoiceItemIngestionArgs]]]:
        suffix_to_args: dict[
            str, Union[InvoiceIngestionArgs, InvoiceItemIngestionArgs]
        ] = {
            "NFe_NotaFiscal": InvoiceIngestionArgs,
            "NFe_NotaFiscalItem": InvoiceItemIngestionArgs,
        }

        ingestion_args_map: Dict[
            str, Union[list[InvoiceIngestionArgs], list[InvoiceItemIngestionArgs]]
        ] = dict()
        for suffix in suffix_to_args.keys():
            ingestion_args_map[suffix] = list()

        for file_path in file_paths:
            matched = False
            file_name = os.path.basename(file_path)
            for suffix, args_class in suffix_to_args.items():
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
                        args_class(file_path=file_path, document_class=document_class)
                    )
                    break
            if not matched:
                message = (
                    f"Warning: File {file_name} does not match expected format "
                    "(YYYYMM_NFe_NotaFiscal.csv or YYYYMM_NFe_NotaFiscalItem.csv)"
                )
                logger.warning(message)

        logger.info(
            f"Files {file_paths} were mapped to ingestion args successfully: {ingestion_args_map}"
        )
        return ingestion_args_map
