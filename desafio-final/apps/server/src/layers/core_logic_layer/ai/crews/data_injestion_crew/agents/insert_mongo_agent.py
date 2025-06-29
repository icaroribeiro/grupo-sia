from crewai import LLM, Agent
from crewai.tools import BaseTool


class InsertMongoAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self, tools: list[BaseTool] = list()) -> Agent:
        return Agent(
            role="""
                Insert Mongo Agent.
            """,
            goal="""
                Insert validated CSV data into MongoDB for InvoiceDocument and InvoiceItemDocument.
            """,
            backstory="""
                You are a database management specialist, skilled at inserting data into MongoDB database.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
            tools=tools,
        )
