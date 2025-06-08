import asyncio
import os
import shutil
from typing import Dict, List

# import litellm
import pandas as pd
from ai_agents_crew.settings.settings import get_settings
from crewai import LLM
from dotenv import load_dotenv

from ai_agents_crew.crews.csv_reading_crew import CSVReadingCrew
from ai_agents_crew.crews.data_analysis_crew import DataAnalysisCrew
from ai_agents_crew.crews.file_unzipping_crew import FileUnzippingCrew
from ai_agents_crew.crews.report_generation_crew import ReportGenerationCrew
from ai_agents_crew.llms import get_llm
from ai_agents_crew.logger.logger import logger

load_dotenv()

# litellm.set_verbose = True
# os.environ["LOG_LEVEL"] = "DEBUG"


class CrewOrchestrator:
    async def run_orchestration(self, llm: LLM, user_query: str) -> str:
        """
        Orchestrates the multi-agent data processing workflow.
        """
        data_dir = get_settings().DATA_DIR
        if not os.path.exists(data_dir):
            logger.error(f"Data directory not found: {data_dir}")
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        zip_files_to_process: List[str] = list()
        for entry in os.listdir(data_dir):
            zip_files_to_process.append(os.path.join(data_dir, entry))

        extracted_dir = os.path.join(data_dir, "extracted")

        if os.path.exists(extracted_dir):
            shutil.rmtree(extracted_dir)
        os.makedirs(extracted_dir, exist_ok=True)

        extracted_csv_paths = await self.__run_step_1(
            llm=llm,
            extracted_dir=extracted_dir,
            zip_files_to_process=zip_files_to_process,
        )

        logger.info(f"Result from Step 1: {extracted_csv_paths}")

        if not extracted_csv_paths:
            return ""

        dataframes_dict = await self.__run_step_2(
            llm=llm,
            extracted_csv_paths=extracted_csv_paths,
        )

        logger.info(f"Result from Step 2: {dataframes_dict}")

        if not dataframes_dict:
            return ""

        analysis_summary = await self.__run_step_3(
            llm=llm, user_query=user_query, dataframes_dict=dataframes_dict
        )

        logger.info(f"Result from Step 3: {analysis_summary}")

        if not analysis_summary:
            return ""

        final_report = await self.__run_step_4(
            llm=llm, user_query=user_query, analysis_summary=analysis_summary
        )

        logger.info(f"Result from Step 4: {final_report}")

        # if os.path.exists(extracted_dir):
        #     shutil.rmtree(extracted_dir)
        # print(f"Cleaned up extracted files in '{extracted_dir}'.")

        return final_report

    @staticmethod
    async def __run_step_1(
        llm: LLM, zip_files_to_process: List[str], extracted_dir: str
    ) -> List[str]:
        """
        Step 1: Running File Unzipping Crew asynchronously...
        """
        logger.info("Step 1: Running File Unzipping Crew asynchronously...")
        try:
            file_unzipping_crew = FileUnzippingCrew(llm=llm).kickoff_crew(
                zip_files_to_process=zip_files_to_process, extracted_dir=extracted_dir
            )
            file_unzipping_crew_result = await file_unzipping_crew.kickoff_async()
            logger.info(f"File Unzipping Crew result: {file_unzipping_crew_result}")

            if "Error" in file_unzipping_crew_result:
                logger.error("Aborting orchestration. Unzipping failed.")
                return

            extracted_csv_paths = [
                os.path.join(extracted_dir, f)
                for f in os.listdir(extracted_dir)
                if f.endswith(".csv")
            ]

            if not extracted_csv_paths:
                logger.warning(
                    "Aborting orchestration. No CSV files found after unzipping."
                )

            return extracted_csv_paths
        except Exception as err:
            logger.error(
                f"Aborting orchestration. An error occurred in File Unzipping Crew: {err}"
            )
            raise

    @staticmethod
    async def __run_step_2(
        llm: LLM, extracted_csv_paths: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """
        Step 2: Running CSV Reading Crew asynchronously...
        """
        logger.info("Step 2: Running CSV Reading Crew asynchronously...")
        try:
            csv_readering_crew = CSVReadingCrew(llm=llm).kickoff_crew(
                csv_file_paths=extracted_csv_paths
            )
            csv_readering_crew_result = await csv_readering_crew.kickoff_async()
            logger.info(f"CSV Reading Crew result: {csv_readering_crew_result}")

            if "Error" in csv_readering_crew_result:
                logger.error("Aborting orchestration. Some CSV files were unreadable.")

            dataframes_dict: Dict[str, pd.DataFrame] = dict()
            for extracted_csv_path in extracted_csv_paths:
                try:
                    csv_file = os.path.basename(extracted_csv_path)
                    dataframes_dict[csv_file] = pd.read_csv(extracted_csv_path)
                    logger.info(f"Loaded '{csv_file}' into DataFrame successfully!")
                except Exception as err:
                    logger.exception(
                        f"Aborting orchestration. Failed to load {extracted_csv_path} into DataFrame: {err}"
                    )
                    raise

            return dataframes_dict
        except Exception as err:
            logger.exception(
                f"Aborting orchestration. An error occurred in CSV Reading Crew: {err}"
            )
            raise

    @staticmethod
    async def __run_step_3(
        llm: LLM, user_query: str, dataframes_dict: Dict[str, pd.DataFrame]
    ) -> str:
        """
        Step 3: Running Data Analysis Crew asynchronously...
        """
        logger.info("Step 3: Running Data Analysis Crew asynchronously...")
        try:
            data_analysis_crew = DataAnalysisCrew(llm=llm).kickoff_crew(
                user_query=user_query, dataframes_dict=dataframes_dict
            )
            data_analysis_crew_result = await data_analysis_crew.kickoff_async()
            logger.info(f"Data Analysis Crew result: {data_analysis_crew_result}")

            return data_analysis_crew_result
        except Exception as err:
            logger.exception(
                f"Aborting orchestration. An error occurred in Data Analysis Crew: {err}"
            )
            raise

    @staticmethod
    async def __run_step_4(llm: LLM, user_query: str, analysis_summary: str) -> str:
        """
        Step 4: Running Report Generation Crew asynchronously...
        """
        logger.info("Step 4: Running Report Generation Crew asynchronously...")
        try:
            report_generation_crew = ReportGenerationCrew(llm=llm).kickoff_crew(
                user_query=user_query, analysis_summary=analysis_summary
            )
            report_generation_crew_result = await report_generation_crew.kickoff_async()
            logger.info(
                f"Report Generation Crew result: {report_generation_crew_result}"
            )

            return report_generation_crew_result
        except Exception as err:
            logger.exception(
                f"Aborting orchestration. An error occurred in Report Generation Crew: {err}"
            )
            raise


if __name__ == "__main__":
    # Set up LLM
    llm = get_llm()

    # Create Crew Orchestrator
    crew_orchestrator = CrewOrchestrator()

    # Define the user's initial query for analysis
    user_query = (
        "What is the number and series of the invoice with the highest total value?"
    )
    logger.info(
        f"--- Starting Data Processing Orchestration for query: '{user_query}' ---\n"
    )

    # Run the asynchronous orchestration
    response = asyncio.run(
        crew_orchestrator.run_orchestration(user_query=user_query, llm=llm)
    )

    logger.info(f"Crew Orchestrator response: {response}")
    print("--- Data Processing Orchestration Complete! ---")
