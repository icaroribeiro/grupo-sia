from langchain_core.language_models import BaseChatModel

from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent
from src.layers.business_layer.ai_agents.tools.test_tools import (
    CheckStringIsPalindromeTool,
    ConvertToLowerCaseTool,
    CreateRandomNumberTool,
)


class AssistentAgent_1(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(
            name="Assistant_1",
            llm=llm,
            tools=[CreateRandomNumberTool()],
            prompt="""
                You are a helpful assistant tasked with creating random numbers.
                Use the CreateRandomNumberTool to generate a random number when requested.
            """,
        )


class AssistentAgent_2(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(
            name="Assistant_2",
            llm=llm,
            tools=[ConvertToLowerCaseTool()],
            prompt="""
                You are a helpful assistant tasked with converting any string in lowercase.
                Use the ConvertToLowerCaseTool to convert text to lowercase when needed.
            """,
        )


class AssistentAgent_3(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(
            name="Assistant_3",
            llm=llm,
            tools=[CheckStringIsPalindromeTool()],
            prompt="""
                You are a helpful assistant tasked with checking if a string is palindrome.
                Use the CheckStringIsPalindromeTool to check string is palindrome when requested.
            """,
        )
