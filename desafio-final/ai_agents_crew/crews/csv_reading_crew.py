from typing import List

from crewai import LLM, Crew, Process, Task

from ai_agents_crew.agents.csv_reader_agent import CSVReaderAgent
from ai_agents_crew.tasks.verify_csv_task import VerifyCSVTask


class CSVReadingCrew:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def kickoff_crew(self, csv_file_paths: List[str]) -> Crew:
        csv_reader_agent = CSVReaderAgent(llm=self.__llm).create()

        verify_csv_tasks: List[Task] = list()
        for csv_file_path in csv_file_paths:
            verify_csv_tasks.append(
                VerifyCSVTask().create(
                    csv_file_path=csv_file_path, agent=csv_reader_agent
                )
            )

        crew = Crew(
            agents=[csv_reader_agent],
            tasks=verify_csv_tasks,
            process=Process.sequential,
            verbose=True,
        )

        return crew
