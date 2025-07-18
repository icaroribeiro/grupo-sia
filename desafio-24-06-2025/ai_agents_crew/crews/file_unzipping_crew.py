from crewai import LLM, Crew, Process

from ai_agents_crew.agents.file_unzipper_agent import FileUnzipperAgent
from ai_agents_crew.tasks.unzip_file_task import UnzipFileTask
from ai_agents_crew.tools.unzip_file_tool import UnzipFileTool


class FileUnzippingCrew:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def kickoff_crew(self, zip_file_to_process: str, extracted_dir: str) -> Crew:
        unzip_file_tool = UnzipFileTool()

        file_unzipper_agent = FileUnzipperAgent(llm=self.__llm).create(
            tools=[unzip_file_tool]
        )

        unzip_file_task = UnzipFileTask().create(
            zip_file_to_process=zip_file_to_process,
            extracted_dir=extracted_dir,
            agent=file_unzipper_agent,
        )

        crew = Crew(
            agents=[file_unzipper_agent],
            tasks=[unzip_file_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew
