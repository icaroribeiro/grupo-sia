from crewai import LLM, Crew, Process

from ai_agents_crew.agents.report_generator_agent import ReportGeneratorAgent
from ai_agents_crew.tasks.generate_report_task import GenerateReportTask


class ReportGenerationCrew:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def kickoff_crew(self, user_query: str, analysis_summary: str) -> Crew:
        report_generator_agent = ReportGeneratorAgent(llm=self.__llm).create()

        generate_report_task = GenerateReportTask().create(
            user_query=user_query,
            analysis_summary=analysis_summary,
            agent=report_generator_agent,
        )

        crew = Crew(
            agents=[report_generator_agent],
            tasks=[generate_report_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew
