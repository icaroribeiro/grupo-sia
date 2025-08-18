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
                            "column_4",
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
                            "column_3",
                            "column_4",
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
                        names=["employee_id", "job_title", "column_3"],
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
                        names=["register", "value", "column_3"],
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

        # Part 1
        # ----------
        custom_prefix: str = """
            You are an assistant specialized in efficiently data processing with Pandas framework.
            You have access to the following pandas DataFrames to perform your activities:

                {dataframes_descriptions}
            """
        dataframes_list = []
        sorted_items = sorted(
            {
                1: "active_employee_data",
                2: "employee_admission_data",
                3: "employee_dismissal_data",
            }.items()
        )
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key}. df{key} ({df_params.name}) {df_params.description}"
                if key == 1
                else f"                {key}. df{key} ({df_params.name}) {df_params.description}"
            )
        formatted_custom_prefix: str = custom_prefix.format(
            dataframes_descriptions="\n".join(dataframes_list),
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")

        custom_suffix = """
            Critical rules:
            - Execute all steps provided in the prompt in the correct order.
            - Do not ask for confirmation or provide intermediate results.
            - Once all steps are complete, save the dfPartial DataFrame as a CSV file and return the final answer.
            """
        logger.info(f"custom_suffix:\n{custom_suffix}")

        input: str = """
            Your task is to gather data from dataframes and consolidate a single basis for purchasing meal value:
            To do this, perform the following steps in order:

            1. From the df1 and df2 DataFrames, do the following tasks:
            - You must rename 'job_title' column of df1 DataFrame to 'job_title_df1' and 'job_title' column of df2 DataFrame to 'job_title_df2'
            - You must perform LEFT merge (Left Outer Join) operation with df1 and df2 DataFrames on 'employee_id' column to join both dataframes;
            - You must identify if there are any rows in the df2 DataFrame that do not exist in the df1 DataFrame based on 'employee_id' columns and concatenate them if any.
            2. From the resulting and df3 DataFrames, do the following tasks:
            - You must perform LEFT merge (Left Outer Join) operation with the resulting and df3 DataFrame on 'employee_id' column to join both dataframes;
            - You must identify if there are any rows in the df3 DataFrame that do not exist in the LEFT DataFrame based on 'employee_id' columns and concatenate them if any.
            3. From the resulting DataFrame, do the following tasks: 
            - You must generate a new DataFrame only with the following columns from resulting DataFrame in order:
                - 'employee_id'
                - 'admission_date'
                - 'job_title_df1'
                - 'job_title_df2'
                - 'termination_date'
                - 'termination_notice'
           
            After performing the steps, you MUST save the new DataFrame to a CSV file at the path '{output_path}'.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_1.csv"
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")

        agent_df_partial_1 = create_pandas_dataframe_agent(
            llm=llm.chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )

        result = agent_df_partial_1.invoke(input=formatted_input)
        logger.info(f"result: {result}")

        # Part 2
        # ----------
        custom_prefix: str = """
            You are an assistant specialized in efficiently data processing with Pandas framework.
            You have access to the following pandas DataFrames to perform your activities:

                {dataframes_descriptions}
            """
        dataframes_list = []
        sorted_items = sorted(
            {
                1: "active_employee_data",
                2: "employee_admission_data",
                3: "employee_dismissal_data",
            }.items()
        )
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key}. df{key} ({df_params.name}) {df_params.description}"
                if key == 1
                else f"                {key}. df{key} ({df_params.name}) {df_params.description}"
            )
        formatted_custom_prefix: str = custom_prefix.format(
            dataframes_descriptions="\n".join(dataframes_list),
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")

        custom_suffix = """
            Critical rules:
            - Execute all steps provided in the prompt in the correct order.
            - Do not ask for confirmation or provide intermediate results.
            - Once all steps are complete, save the dfPartial DataFrame as a CSV file and return the final answer.
            """
        logger.info(f"custom_suffix:\n{custom_suffix}")

        input: str = """
            Your task is to gather data from dataframes and consolidate a single basis for purchasing meal value:
            To do this, perform the following steps in order:


                    #     3. From the resulting and df3 DataFrames, do the following tasks:
        #     - You must rename 'job_title' column of df3 DataFrame to 'job_title_df3'
        #     - You must perform LEFT merge (Left Outer Join) operation with the resulting and df3 DataFrames on 'employee_id' column to join both dataframes;
        #     - You must identify if there are any rows in the df3 DataFrame that do not exist in the LEFT DataFrame based on 'employee_id' columns and concatenate them if any.
        #     4. From the resulting and df6 DataFrames, do the following tasks:
        #     - You must rename 'job_title' column of df6 DataFrame to 'job_title_df6'
        #     - You must perform LEFT merge (Left Outer Join) operation with the resulting and df6 DataFrames on 'employee_id' column to join both dataframes;
        #     - You must identify if there are any rows in the df6 DataFrame that do not exist in the LEFT DataFrame based on 'employee_id' columns and concatenate them if any.
        #     5. From the resulting and df8 DataFrames, do the following tasks:
        #     - You must rename 'situation_desc' column of df8 DataFrame to 'situation_desc_df8'
        #     - You must perform LEFT merge (Left Outer Join) operation with the resulting and df8 DataFrames on 'employee_id' column to join both dataframes;
        #     - You must identify if there are any rows in the df8 DataFrame that do not exist in the LEFT DataFrame based on 'employee_id' columns and concatenate them if any.
        #     6. From the resulting and df2 DataFrames, do the following tasks:
        #     - You must rename 'situation_desc' column of df2 DataFrame to 'situation_desc_df2'
        #     - You must add 'absense_days' column to df2 DataFrame and fill all its rows with the value 0
        #     - You must perform LEFT merge (Left Outer Join) operation with the resulting and df2 DataFrames on 'employee_id' column to join both dataframes;
        #     - You must identify if there are any rows in the df2 DataFrame that do not exist in the LEFT DataFrame based on 'employee_id' columns and concatenate them if any.
        #     7. From the resulting DataFrame, do the following tasks:
        #     - You must generate a new DataFrame (dfPartial) only with the following columns from resulting DataFrame in order:
        #         - 'employee_id'
        #         - 'admission_date'
        #         - 'job_title_df4'
        #         - 'job_title_df1'
        #         - 'termination_date'
        #         - 'termination_notice'
        #         - 'job_title_df3'
        #         - 'job_title_df6'
        #         - 'situation_desc_df8'
        #         - 'vacation_days'
        #         - 'situation_desc_df2'
        #         - 'absense_days'
        #     8. From the dfPartial DataFrame, do the following tasks:
        #     - You must generate a new DataFrame (dfFinal) only with the following columns from dfPartial DataFrame in order:
        #         - 'employee_id'
        #         - 'admission_date'
        #         - 'job_title_df4'
        #         - 'job_title_df1'
        #         - 'termination_date'
        #         - 'termination_notice'
        #         - 'job_title_df3'
        #         - 'job_title_df6'
        #         - 'situation_desc_df8'
        #         - 'vacation_days'
        #         - 'situation_desc_df2'
        #         - 'absense_days'


                   
            After performing the steps, you MUST save the new DataFrame to a CSV file at the path '{output_path}'.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_2.csv"
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")

        agent_df_partial_1 = create_pandas_dataframe_agent(
            llm=llm.chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )

        result = agent_df_partial_1.invoke(input=formatted_input)
        logger.info(f"result: {result}")

        # custom_prefix: str = """
        #     You are an assistant specialized in efficiently data processing.
        #     You have access to the following pandas DataFrames to perform your activities:

        #         {dataframes_descriptions}
        #     """
        # dataframes_list = []
        # sorted_items = sorted(
        #     {
        #         0: "employee_admission_data",
        #         1: "employee_absense_data",
        #         2: "apprentice_employee_data",
        #         3: "active_employee_data",
        #         4: "employee_dismissal_data",
        #         5: "intern_employee_data",
        #         6: "employee_abroad_data",
        #         7: "employee_vacation_data",
        #         8: "syndicate_data",
        #     }.items()
        # )
        # for key, value in sorted_items:
        #     df_params = dataframes_dict[value]
        #     dataframes_list.append(
        #         f"{key}. df{key} ({df_params.name}) {df_params.description}"
        #         if key == 1
        #         else f"                {key}. df{key} ({df_params.name}) {df_params.description}"
        #     )
        # formatted_custom_prefix: str = custom_prefix.format(
        #     dataframes_descriptions="\n".join(dataframes_list),
        # )
        # logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")

        # custom_suffix = """
        #     Critical rules:
        #     - Execute all steps provided in the prompt in the correct order.
        #     - Do not ask for confirmation or provide intermediate results.
        #     - Once all steps are complete, save the dfPartial DataFrame as a CSV file and return the final answer.
        #     """
        # logger.info(f"custom_suffix:\n{custom_suffix}")

        # input: str = """
        #     Your task is to gather data from dataframes and consolidate a single basis for purchasing meal value:
        #     To do this, perform the following steps in order:

        #     1. From the df4 and df1 DataFrames, do the following tasks:
        #     - You must rename 'job_title' column of df4 DataFrame to 'job_title_df4' and 'job_title' column of df1 DataFrame to 'job_title_df1'
        #     - You must perform LEFT merge (Left Outer Join) operation with df4 and df1 DataFrames on 'employee_id' column to join both dataframes;
        #     - You must identify if there are any rows in the df1 DataFrame that do not exist in the df4 DataFrame based on 'employee_id' columns and concatenate them if any.
        #     2. From the resulting and df5 DataFrames, do the following tasks:
        #     - You must perform LEFT merge (Left Outer Join) operation with the resulting and df5 DataFrame on 'employee_id' column to join both dataframes;
        #     - You must identify if there are any rows in the df5 DataFrame that do not exist in the LEFT DataFrame based on 'employee_id' columns and concatenate them if any.
        #     After performing the steps, you MUST save dfFinal DataFrame to a CSV file at the path '{output_path}'.
        #     """
        # formatted_input: str = input.format(
        #     output_path=os.path.join(),
        # )
        # logger.info(f"formatted_input: {formatted_input}")

        # agent_df_partial_1 = create_pandas_dataframe_agent(
        #     llm=llm.chat_model,
        #     df=[dataframes_dict[value].content for _, value in sorted_items],
        #     agent_type=AgentType.OPENAI_FUNCTIONS,
        #     allow_dangerous_code=True,
        #     prefix=formatted_custom_prefix,
        #     suffix=custom_suffix,
        #     verbose=False,
        #     max_iterations=100,
        #     max_execution_time=300,
        # )

        # result = agent_df_partial_1.invoke(input=formatted_input)
        # logger.info(f"result: {result}")
