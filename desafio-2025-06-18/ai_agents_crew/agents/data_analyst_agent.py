from typing import List
from crewai import LLM, Agent
from crewai.tools import BaseTool


class DataAnalystAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self, tools: List[BaseTool] = list()) -> Agent:
        return Agent(
            role="""
                Senior Data Analyst
            """,
            goal="""
                Perform in-depth analysis on provided dataframes based on user queries and 
                extract key insights.
            """,
            backstory="""
                You are a meticulous data scientist with a knack for finding hidden patterns and 
                providing clear, actionable insights from complex datasets.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
            tools=tools,
        )
