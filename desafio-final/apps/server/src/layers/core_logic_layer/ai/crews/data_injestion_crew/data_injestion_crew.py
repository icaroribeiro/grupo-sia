from src.layers.core_logic_layer.ai.agents.csv_validation_agent import (
    CSVValidatorAgent,
)
from crewai import LLM, Crew, Process

from src.layers.core_logic_layer.ai.agents.file_unzip_agent import UnzipFileAgent
from src.layers.core_logic_layer.ai.crews.data_injestion_crew.tasks import (
    insert_mongo_task,
)
from src.layers.core_logic_layer.ai.tools.unzip_file_tool import UnzipFileTool

from src.layers.core_logic_layer.ai.tasks.unzip_file_task import UnzipFileTask


class DataInjestionCrew:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def kickoff_crew(self, zip_path: str, csv_dir_path: str) -> Crew:
        unzip_file_tool = UnzipFileTool()
        unzip_file_agent = UnzipFileAgent(llm=self.__llm).create(
            tools=[unzip_file_tool]
        )
        unzip_file_task = UnzipFileTask().create(
            zip_path=zip_path,
            csv_dir_path=csv_dir_path,
            agent=unzip_file_agent,
        )

        csv_validator_agent = CSVValidatorAgent(llm=self.__llm).create()
        validate_csv_task_conten
        validate_csv_task = ValidateCSVTask().create(
            csv_dir_path=csv_dir_path,
            agent=csv_validator_agent,
            context=context,
        )

        crew = Crew(
            agents=[unzip_file_agent, validate_csv_agent, insert_mongo_agent],
            tasks=[unzip_file_task, validate_csv_task, insert_mongo_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew
