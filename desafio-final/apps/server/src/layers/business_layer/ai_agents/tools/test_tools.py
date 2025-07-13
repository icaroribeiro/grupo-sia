import random
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class CreateRandomNumberTool(BaseTool):
    name: str = "create_random_number_tool"
    description: str = """
    Return a number between 0 and 100.
    """

    def _run(self) -> str:
        return random.randint(0, 100)


class ToLowerCaseInput(BaseModel):
    """Input schema for ToLowerCaseTool."""

    input: str = Field(..., description="String to convert to lower case.")


class ToLowerCaseTool(BaseTool):
    name: str = "to_lower_case_tool"
    description: str = """
    Return input string to lower case.
    """
    args_schema: Type[BaseModel] = ToLowerCaseInput

    def _run(self, input: str) -> str:
        return input.lower()


class CountCharsInput(BaseModel):
    """Input schema for CountCharsTool."""

    input: str = Field(..., description="String to count its chars.")


class CountCharsTool(BaseTool):
    name: str = "count_chars_tool"
    description: str = """
    Return input string to lower case.
    """
    args_schema: Type[BaseModel] = CountCharsInput

    def _run(self, input: str) -> int:
        return len(input)


class GetIcarosAgeTool(BaseTool):
    name: str = "get_icaros_age_tool"
    description: str = """
    Return Icaro's age.
    """

    def _run(self) -> int:
        return 36
