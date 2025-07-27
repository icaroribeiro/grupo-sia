from langchain_core.language_models import BaseChatModel

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate


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
