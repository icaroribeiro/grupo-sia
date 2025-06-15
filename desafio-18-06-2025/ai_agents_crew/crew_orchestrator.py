import asyncio
import os
from typing import Dict, List, Optional, Tuple

# import litellm
import pandas as pd
from crewai import LLM
from dotenv import load_dotenv

from ai_agents_crew.crews.csv_reading_crew import CSVReadingCrew
from ai_agents_crew.crews.data_analysis_crew import DataAnalysisCrew
from ai_agents_crew.crews.file_unzipping_crew import FileUnzippingCrew
from ai_agents_crew.crews.report_generation_crew import ReportGenerationCrew
from ai_agents_crew.llms import get_llm
from ai_agents_crew.logger.logger import logger
import csv
import tempfile
import zipfile

load_dotenv()

# litellm.set_verbose = True
# os.environ["LOG_LEVEL"] = "DEBUG"


class CrewOrchestrator:
    async def run_orchestration(
        self,
        llm: LLM,
        user_query: str,
        file_path: Optional[str] = None,
        cached_dataframes_dict: Optional[dict] = None,
    ) -> Tuple[bool, str]:
        """
        Orchestrates the multi-agent data processing workflow.
        Reuses DataFrames in cache if available.
        """
        dataframes_dict: Dict[str, pd.DataFrame] = dict()
        if cached_dataframes_dict:
            logger.info("DataFrames reloaded from cache.")
            dataframes_dict = cached_dataframes_dict
        else:
            if file_path:
                data_dir = os.path.dirname(file_path)
                extracted_dir = os.path.join(data_dir, "extracted")
                extracted_csv_paths = await self.__run_step_1(
                    llm=llm,
                    extracted_dir=extracted_dir,
                    zip_file_to_process=file_path,
                )

                logger.info(f"Result from Step 1: {extracted_csv_paths}")

                if not extracted_csv_paths:
                    err = f"Nenhum arquivo CSV foi extraído do arquivo .zip {os.path.basename(file_path)}."
                    return False, err

                dataframes_dict = await self.__run_step_2(
                    llm=llm,
                    extracted_csv_paths=extracted_csv_paths,
                )

                logger.info(f"Result from Step 2: {dataframes_dict}")

                if not dataframes_dict:
                    err = f"Erro ao ler arquivos CSV extraídos do arquivo .zip {os.path.basename(file_path)}."
                    return False, err

                # Save DataFrames in session cache.
                cached_dataframes_dict = dataframes_dict

        analysis_summary = await self.__run_step_3(
            llm=llm, user_query=user_query, dataframes_dict=dataframes_dict
        )

        logger.info(f"Result from Step 3: {analysis_summary}")

        if not analysis_summary:
            err = "Não foi possível gerar uma análise com os dados fornecidos."
            return False, err

        final_report = await self.__run_step_4(
            llm=llm, user_query=user_query, analysis_summary=analysis_summary
        )

        logger.info(f"Result from Step 4: {final_report}")

        return True, final_report

    @staticmethod
    async def __run_step_1(
        llm: LLM, zip_file_to_process: str, extracted_dir: str
    ) -> List[str]:
        """
        Step 1: Running File Unzipping Crew asynchronously...
        """
        logger.info("Step 1: Running File Unzipping Crew asynchronously...")
        try:
            file_unzipping_crew = FileUnzippingCrew(llm=llm).kickoff_crew(
                zip_file_to_process=zip_file_to_process, extracted_dir=extracted_dir
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
                    "Aborting orchestration. No CSV file found after unzipping."
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


def create_temporary_zip_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_file_path = os.path.join(temp_dir, "YYYYMM_NFs_Itens.csv")

        data = [
            {"NÚMERO PRODUTO": "P001", "VALOR TOTAL": 100.50},
            {"NÚMERO PRODUTO": "P002", "VALOR TOTAL": 250.75},
            {"NÚMERO PRODUTO": "P003", "VALOR TOTAL": 89.99},
            {"NÚMERO PRODUTO": "P004", "VALOR TOTAL": 150.25},
            {"NÚMERO PRODUTO": "P005", "VALOR TOTAL": 300.00},
        ]

        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=["NÚMERO PRODUTO", "VALOR TOTAL"]
            )
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        zip_path = temp_zip.name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(csv_file_path, os.path.basename(csv_file_path))

        return zip_path


async def main():
    # Set up LLM
    llm = get_llm()

    # Create Crew Orchestrator
    crew_orchestrator = CrewOrchestrator()

    # Define the user's initial query for analysis
    user_query = "What is the item with the highest total value?"
    logger.info(
        f"--- Starting Data Processing Orchestration for query: '{user_query}' ---\n"
    )

    # Create temporary .zip file
    zip_path = create_temporary_zip_file()

    # Run the asynchronous orchestration
    _, response = await crew_orchestrator.run_orchestration(
        user_query=user_query,
        llm=llm,
        file_path=zip_path,
        cached_dataframes_dict=None,
    )

    logger.info(f"Crew Orchestrator response: {response}")
    print("--- Data Processing Orchestration Complete! ---")


if __name__ == "__main__":
    asyncio.run(main())
