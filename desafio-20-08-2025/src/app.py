import os

import pandas as pd
from langchain.agents.agent_types import AgentType
from pydantic import BaseModel
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import ai_settings, app_settings
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


class DataFrameParams(BaseModel):
    name: str
    description: str
    content: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True


def create_input_dataframes_from_files(
    directory_path: str,
) -> dict[str, DataFrameParams]:
    """
    Reads all specific XLSX files from a directory and creates a dictionary of DataFrameParams objects.

    params:
        directory_path: The path to the folder containing the XLSX files.

    Returns:
        A dictionary where keys are DataFrame names and values are DataFrameParams objects.
    """
    dataframes_dict = {}
    syndicate_parts = {}

    for filename in os.listdir(directory_path):
        if filename.endswith(".xlsx"):
            file_path = os.path.join(directory_path, filename)

            match filename:
                case "ADMISSÃO ABRIL.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id",
                            "admission_date",
                            "job_title",
                            "column_header_4",
                        ],
                        index_col=None,
                    )
                    # Drop the last column using iloc
                    # df = df.iloc[:, :-1]
                    dataframes_dict["employee_admission_data"] = DataFrameParams(
                        name="employee_admission_data", description="", content=df
                    )
                case "AFASTAMENTOS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id",
                            "situation_desc",
                            "column_header_3",
                            "column_header_4",
                        ],
                        index_col=None,
                    )
                    # Drop the last two columns using iloc
                    # df = df.iloc[:, :-2]
                    dataframes_dict["employee_absense_data"] = DataFrameParams(
                        name="employee_absense_data", description="", content=df
                    )
                case "APRENDIZ.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=["employee_id", "job_title"],
                        index_col=None,
                    )
                    dataframes_dict["apprentice_employee_data"] = DataFrameParams(
                        name="apprentice_employee_data", description="", content=df
                    )
                case "ATIVOS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id",
                            "company_id",
                            "job_title",
                            "situation_desc",
                            "syndicate_name",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["active_employee_data"] = DataFrameParams(
                        name="active_employee_data",
                        description="Base dataframe for building the single database for meal value purchases.",
                        content=df,
                    )
                case "Base dias uteis.xlsx":
                    syndicate_parts["syndicate_working_days"] = pd.read_excel(
                        file_path,
                        header=1,
                        names=["name", "working_days"],
                        index_col=None,
                    ).dropna()
                case "Base sindicato x valor.xlsx":
                    syndicate_parts["syndicate_meal_voucher_value"] = pd.read_excel(
                        file_path,
                        header=0,
                        names=["state", "meal_voucher_value"],
                        index_col=None,
                    ).dropna()
                case "DESLIGADOS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=["employee_id", "termination_date", "termination_notice"],
                        index_col=None,
                    )
                    dataframes_dict["employee_dismissal_data"] = DataFrameParams(
                        name="employee_dismissal_data", description="", content=df
                    )
                case "ESTÁGIO.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=["employee_id", "job_title", "column_header_3"],
                        index_col=None,
                    )
                    # Drop the last column using iloc
                    # df = df.iloc[:, :-1]
                    dataframes_dict["intern_employee_data"] = DataFrameParams(
                        name="intern_employee_data", description="", content=df
                    )
                case "EXTERIOR.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=["register", "value", "column_header_3"],
                        index_col=None,
                    )
                    # Drop the last two columns using iloc
                    # df = df.iloc[:, :-2]
                    dataframes_dict["employee_abroad_data"] = DataFrameParams(
                        name="employee_abroad_data", description="", content=df
                    )
                case "FÉRIAS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=["employee_id", "situation_desc", "vacation_days"],
                        index_col=None,
                    )
                    dataframes_dict["employee_vacation_data"] = DataFrameParams(
                        name="employee_vacation_data", description="", content=df
                    )

    # Create the initial part of the syndicate_data
    SYNDICATE_STATE_MAPPING: dict[str, str] = {
        "Paraná": "SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS DE CURITIBA E REGIAO METROPOLITANA",
        "Rio Grande do Sul": "SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL",
        "São Paulo": "SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.",
        "Rio de Janeiro": "SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS DO RIO DE JANEIRO",
    }
    syndicate_df = pd.DataFrame.from_dict(
        SYNDICATE_STATE_MAPPING, orient="index", columns=["state"]
    ).reset_index()
    syndicate_df.columns = ["state", "name"]
    syndicate_df = syndicate_df.dropna()

    # Merge the syndicate parts if they were successfully loaded
    if "syndicate_meal_voucher_value" in syndicate_parts:
        syndicate_df = pd.merge(
            syndicate_df,
            syndicate_parts["syndicate_meal_voucher_value"],
            on="state",
            how="inner",
        )

    if "syndicate_working_days" in syndicate_parts:
        syndicate_df = pd.merge(
            syndicate_df,
            syndicate_parts["syndicate_working_days"],
            on="name",
            how="inner",
        )

    # Add the final syndicate DataFrame to the dictionary
    dataframes_dict["syndicate_data"] = DataFrameParams(
        name="syndicate_data", description="", content=syndicate_df
    )

    # Save each DataFrame to a CSV file and return the dictionary
    output_dir = app_settings.output_data_dir_path
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for name, df_params in dataframes_dict.items():
        if not df_params.content.empty:
            df_params.content.to_csv(
                os.path.join(output_dir, f"{name}.csv"), index=False
            )

    return dataframes_dict


class App:
    def __init__(self) -> None:
        self._container = Container()

    @staticmethod
    def run() -> None:
        llm = LLM(ai_settings=ai_settings)

        dataframes_dict: dict[str, DataFrameParams] = (
            create_input_dataframes_from_files(app_settings.input_data_dir_path)
        )

        custom_prefix: str = """
            You are an assistant specialized in efficiently data processing.
            You have access to the following pandas DataFrames to perform your activities:

                {dataframes_descriptions}
            """
        dataframes_list = []
        sorted_items = sorted(
            {
                0: "employee_admission_data",
                1: "employee_absense_data",
                2: "apprentice_employee_data",
                3: "active_employee_data",
                4: "employee_dismissal_data",
                5: "intern_employee_data",
                6: "employee_abroad_data",
                7: "employee_vacation_data",
                8: "syndicate_data",
            }.items()
        )
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key + 1}. df{key + 1} ({df_params.name}) {df_params.description}"
                if key == 0
                else f"                {key + 1}. df{key + 1} ({df_params.name}) {df_params.description}"
            )
        formatted_custom_prefix: str = custom_prefix.format(
            dataframes_descriptions="\n".join(dataframes_list),
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")

        custom_suffix = """
            After performing your tasks, rename the columns in resulting dataframe to their Portuguese translations as follows:
            - 'employee_id' should be translated to 'Matricula'
            - 'syndicate_name' should be translated to 'Sindicato do Colaborador'

            Finally, save the resulting dataframe to a CSV file at the path '{output_path}'.
            
            Ensure the CSV file is properly formatted, with no index column included in the output.
            """
        formatted_custom_suffix: str = custom_suffix.format(
            output_path=os.path.join(
                app_settings.output_data_dir_path, "VR MENSAL 05.2025_FINAL.csv"
            ),
        )
        logger.info(f"formatted_custom_suffix:\n{formatted_custom_suffix}")

        meal_voucher_dataframe_agent = create_pandas_dataframe_agent(
            llm=llm.chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=formatted_custom_suffix,
            verbose=True,
        )

        input: str = """
            Your task is to gather data from dataframes and consolidate a single basis for purchasing meal value:
            To do this, perform the following steps in order:

            1. From the df4 DataFrame, you must filter and remove only the rows where the value in the 'job_title' column contains a substring 'DIRETOR';
            2. From the the resulting DataFrame, do the folowing tasks:
            - You must filter only the rows where the value in the 'employee_id' column is the equal to the value in the 'employee_id' column of df6 Dataframe;
            - You must filter only the rows where the value in the 'job_title' column is 'ESTAGIARIO';
            - You must remove the selected rows.
            3. From the the resulting DataFrame, do the folowing tasks:
            - You must filter only the rows where the value in the 'employee_id' column is the equal to the value in the 'employee_id' column of df3 Dataframe;
            - You must filter only the rows where the value in the 'job_title' column is 'APRENDIZ';
            - You must remove the selected rows.
            4. From the the resulting DataFrame, do the folowing tasks:
            - You must filter and only the rows where the value in the 'employee_id' column is the equal to the value in the 'employee_id' column of df2 Dataframe;
            - You must remove the selected rows.
            5. From the the resulting DataFrame, do the folowing tasks:
            - You must filter only the rows where the value in the 'employee_id' column is the equal to the value in the 'register' column of df7 Dataframe;
            - You must remove the selected rows.
            # Dismissal rules:
            6. From the resulting DataFrame, do the following tasks:
            - You must perform LEFT merge (Left Outer Join) operation with df5 DataFrame to join both dataframes;
            - You must combine the values in the 'employee_id' column of resulting DataFrame that are equal to the values in the 'employee_id' column of df5 Dataframe.
            - You must combine the values in the 'employee_id' column of resulting DataFrame that are equal to the values in the 'employee_id' column of df5 Dataframe.
            7. Based on the resulting DataFrame, you must generate a new DataFrame only with the following columns in order:
            - 'employee_id'

            """
        logger.info(f"input:\n{input}")

        result = meal_voucher_dataframe_agent.invoke(input=input)
        logger.info(f"result: {result}")

        result = meal_voucher_dataframe_agent.invoke(
            input="Informe uma lista com os números dos dias considerados como 'dias úteis' do calendário em maio de 2025"
        )
        logger.info(f"result: {result}")
