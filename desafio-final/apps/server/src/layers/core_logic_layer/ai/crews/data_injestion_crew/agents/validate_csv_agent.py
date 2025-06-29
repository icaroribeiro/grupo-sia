from crewai import LLM, Agent
from crewai.tools import BaseTool


class ValidateCSVAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self, tools: list[BaseTool] = list()) -> Agent:
        return Agent(
            role="""
                Validate CSV Agent.
            """,
            goal="""
                Validate columns of multiple CSV files against Beanie document models.
            """,
            backstory="""
                You are a data validation and schema matching specialist, skilled at ensuring that CSV files are correctly formatted and match schemas.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
            tools=tools,
        )
