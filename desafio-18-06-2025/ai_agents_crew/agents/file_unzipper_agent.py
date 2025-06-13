from crewai import LLM, Agent
from typing import List
from crewai.tools import BaseTool


class FileUnzipperAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self, tools: List[BaseTool] = list()) -> Agent:
        return Agent(
            role="""
                File Unzipper
            """,
            goal="""
                Extract specified ZIP files and confirm successful extraction.
            """,
            backstory="""
                You are an automated file system assistant, skilled at handling compressed archives.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
            tools=tools,
        )
