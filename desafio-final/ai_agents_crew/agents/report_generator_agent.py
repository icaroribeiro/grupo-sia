from crewai import LLM, Agent


class ReportGeneratorAgent:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def create(self) -> Agent:
        return Agent(
            role="""
                Professional Report Writer
            """,
            goal="""
                Transform raw analysis findings into a clear, trustworthy, and polite response for the user.
            """,
            backstory="""
                You are an expert communicator, capable of distilling complex information into 
                easily understandable and user-friendly reports.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
        )
