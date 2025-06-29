from crewai import LLM, Agent
from crewai.tools import BaseTool


class UnzipFileAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self, tools: list[BaseTool] = list()) -> Agent:
        return Agent(
            role="""
                Unzip File Agent.
            """,
            goal="""
                Extract all CSV files from a ZIP archive to a specified directory.
            """,
            backstory="""
                You are an automated file system specialist, skilled at handling compressed archives.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
            tools=tools,
        )
