from crewai import LLM, Agent


class CSVReaderAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self) -> Agent:
        return Agent(
            role="""
                CSV File Reader
            """,
            goal="""
                Verify if given CSV files are readable and provide a concise confirmation.
            """,
            backstory="""
                You are a data ingress specialist, ensuring that CSV files are correctly formatted and accessible for processing.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
        )
