from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent


class DataIngestionAgent:
    def __init__(self, llm: BaseChatModel, tools: list[BaseTool] = list()):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a Data Ingestion Assistant specialized in efficiently handling data ingestion tasks.
                    You have access to the following tools to perform your activities:
                    {tool_descriptions}
        
                    The input will be a JSON string containing `file_path` and `destination_dir_path`. 
                    Parse the input, extract these fields, and start the workflow by calling the `unzip_files_from_zip_archive_tool` with the provided `file_path` and `destination_dir_path`.
                    If the input is invalid or missing required fields, return an error message.
                    """,
                )
            ]
        )
        formatted_content = prompt.format(
            tool_descriptions="\n".join(
                [f"- `{tool.name}`: {tool.description.strip()}" for tool in tools]
            )
        )
        self.__agent = create_react_agent(
            name="data_ingestion_agent",
            model=llm,
            tools=tools,
            prompt=formatted_content,
        )

    @property
    def agent(self):
        return self.__agent
