import random
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class CreateRandomNumberTool(BaseTool):
    name: str = "create_random_number_tool"
    description: str = """
    Generates a random number between 1 and 100.
    Returns:
        int: The random number.
    """

    def _run(self) -> int:
        logger.info("Generating random number")
        result = random.randint(1, 100)
        logger.info(f"Generated random number: {result}")
        return result

    async def _arun(self) -> str:
        return self._run()


class ToLowerCaseInput(BaseModel):
    """Input schema for ToLowerCaseTool."""

    text: str = Field(..., description="The string to convert to lowercase.")


class ConvertToLowerCaseTool(BaseTool):
    name: str = "convert_to_lower_case_tool"
    description: str = """
    Converts an input string to lowercase.
    Returns:
        str: The lowercase version of the input string
    """
    args_schema: Type[BaseModel] = ToLowerCaseInput

    def _run(self, text: str) -> str:
        logger.info(f"Converting to lowercase: {text}")
        result = text.lower()
        logger.info(f"Converted to: {result}")
        return result

    async def _arun(self, text: str) -> str:
        return self._run(text)


class CountStringCharsInput(BaseModel):
    """Input schema for CountCharsTool."""

    text: str = Field(..., description="The string to count characters for.")


class CountStringCharsTool(BaseTool):
    name: str = "count_string_chars_tool"
    description: str = """
    Counts the number of characters in a string.
    Returns:
        str: The number of characters as a string
    """
    args_schema: Type[BaseModel] = CountStringCharsInput

    def _run(self, text: str) -> str:
        logger.info(f"Counting characters in: {text}")
        result = str(len(text))
        logger.info(f"Character count: {result}")
        return result

    async def _arun(self, text: str) -> str:
        return self._run(text)


class CheckStringIsPalindromeTool(BaseTool):
    name: str = "check_string_is_palindrome_tool"
    description: str = """
    Checks if string is palindrome.
    Returns:
        bool: The assessment if string is palindrome
    """
    args_schema: Type[BaseModel] = CountStringCharsInput

    def _run(self, text: str) -> str:
        logger.info(f"Checking if string is palindrome: {text}")
        result = text == text[::-1]
        logger.info(f"Character count: {result}")
        return result

    async def _arun(self, text: str) -> str:
        return self._run(text)
