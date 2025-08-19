import os

import pandas as pd
from langchain.agents.agent_types import AgentType
from pydantic import BaseModel
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.models.tool_output import Status
from src.layers.business_layer.ai_agents.tools.calculate_absense_days_tool import (
    CalculateAbsenseDaysTool,
)
from src.layers.business_layer.ai_agents.tools.extract_absense_return_date_tool import (
    ExtractAbsenseReturnDateTool,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import ai_settings, app_settings
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent import (
    AgentExecutor,
)


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

    for filename in os.listdir(directory_path):
        if filename.endswith(".xlsx"):
            file_path = os.path.join(directory_path, filename)

            match filename:
                case "ADMISSÃO ABRIL.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_employee_admission_df",
                            "admission_date_employee_admission_df",
                            "job_title_employee_admission_df",
                            "column_4_employee_admission_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["employee_admission_df"] = DataFrameParams(
                        name="employee_admission_df", description="", content=df
                    )
                case "AFASTAMENTOS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_employee_absense_df",
                            "situation_desc_employee_absense_df",
                            "column_3_employee_absense_df",
                            "detail_employee_absense_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["employee_absense_df"] = DataFrameParams(
                        name="employee_absense_df", description="", content=df
                    )
                case "APRENDIZ.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_apprentice_employee_df",
                            "job_title_apprentice_employee_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["apprentice_employee_df"] = DataFrameParams(
                        name="apprentice_employee_df", description="", content=df
                    )
                case "ATIVOS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_active_employee_df",
                            "company_id_active_employee_df",
                            "job_title_active_employee_df",
                            "situation_desc_active_employee_df",
                            "syndicate_name_active_employee_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["active_employee_df"] = DataFrameParams(
                        name="active_employee_df",
                        description="",
                        content=df,
                    )
                case "Base dias uteis.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=1,
                        names=[
                            "name_syndicate_working_days_df",
                            "working_days_syndicate_working_days_df",
                        ],
                        index_col=None,
                    ).dropna()
                    dataframes_dict["syndicate_working_days_df"] = DataFrameParams(
                        name="syndicate_working_days_df",
                        description="",
                        content=df,
                    )
                case "Base sindicato x valor.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "state_syndicate_meal_voucher_value_df",
                            "meal_voucher_value_syndicate_meal_voucher_value_df",
                        ],
                        index_col=None,
                    ).dropna()
                    dataframes_dict["syndicate_meal_voucher_value_df"] = (
                        DataFrameParams(
                            name="syndicate_meal_voucher_value_df",
                            description="",
                            content=df,
                        )
                    )
                case "DESLIGADOS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_employee_dismissal_df",
                            "termination_date_employee_dismissal_df",
                            "termination_notice_employee_dismissal_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["employee_dismissal_df"] = DataFrameParams(
                        name="employee_dismissal_df", description="", content=df
                    )
                case "ESTÁGIO.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_intern_employee_df",
                            "job_title_intern_employee_df",
                            "column_3_intern_employee_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["intern_employee_df"] = DataFrameParams(
                        name="intern_employee_df", description="", content=df
                    )
                case "EXTERIOR.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "register_employee_abroad_df",
                            "value_employee_abroad_df",
                            "column_3_employee_abroad_df",
                        ],
                        index_col=None,
                    )
                    # Drop the last two columns using iloc
                    # df = df.iloc[:, :-2]
                    dataframes_dict["employee_abroad_df"] = DataFrameParams(
                        name="employee_abroad_df", description="", content=df
                    )
                case "FÉRIAS.xlsx":
                    df = pd.read_excel(
                        file_path,
                        header=0,
                        names=[
                            "employee_id_employee_vacation_df",
                            "situation_desc_employee_vacation_df",
                            "vacation_days_employee_vacation_df",
                        ],
                        index_col=None,
                    )
                    dataframes_dict["employee_vacation_df"] = DataFrameParams(
                        name="employee_vacation_df", description="", content=df
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

        # # Part 1
        # # ------------------------------------------------------------------------------
        # custom_prefix: str = """
        #     You are an assistant specialized in software development with Python and efficiently data processing using Pandas library.
        #     You have access to the following pandas DataFrames to perform your activities:

        #         {dataframes_descriptions}
        #     """
        # dataframes_list = []
        # sorted_items = sorted(
        #     {
        #         1: "active_employee_df",
        #         2: "employee_admission_df",
        #         3: "employee_dismissal_df",
        #     }.items()
        # )
        # for key, value in sorted_items:
        #     df_params = dataframes_dict[value]
        #     dataframes_list.append(
        #         f"{key}. df{key} ({df_params.name})"
        #         if key == 1
        #         else f"                {key}. df{key} ({df_params.name})"
        #     )
        # formatted_custom_prefix: str = custom_prefix.format(
        #     dataframes_descriptions="\n".join(dataframes_list),
        # )
        # logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")

        # custom_suffix = """
        #     Critical rules:
        #     - Execute all steps provided in the prompt in the correct order.
        #     - Do not ask for confirmation or provide intermediate results.
        #     - Once all steps are complete, save the `resulting` DataFrame to a CSV file and return the final answer.
        #     """
        # logger.info(f"custom_suffix:\n{custom_suffix}")

        # input: str = """
        #     Your task is to process data and save the `resulting` DataFrame to a CSV file.

        #     To do this, perform the following steps in order:

        #     1. From the `df1` (active_employee_df) and `df2` (employee_admission_df) DataFrames:
        #     - Rename the `employee_id_active_employee_df` column of the `df1` DataFrame to `employee_id`.
        #     - Rename the `employee_id_employee_admission_df` column of the `df2` DataFrame to `employee_id`.
        #     - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
        #     - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

        #     2. From the `resulting` and `df3` (employee_dismissal_df) DataFrames:
        #     - Rename the `employee_id_employee_dismissal_df` column of the `df1` DataFrame to `employee_id`.
        #     - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
        #     - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

        #     3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
        #     """
        # formatted_input: str = input.format(
        #     output_path=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_1.csv"
        #     ),
        # )
        # logger.info(f"formatted_input: {formatted_input}")

        # assistant = create_pandas_dataframe_agent(
        #     llm=llm.chat_model,
        #     df=[dataframes_dict[value].content for _, value in sorted_items],
        #     agent_type=AgentType.OPENAI_FUNCTIONS,
        #     allow_dangerous_code=True,
        #     prefix=formatted_custom_prefix,
        #     suffix=custom_suffix,
        #     verbose=True,
        # )

        # result = assistant.invoke({"input": formatted_input})
        # logger.info(f"result: {result}")

        # # Part 2
        # # ------------------------------------------------------------------------------
        # df = pd.read_csv(
        #     filepath_or_buffer=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_1.csv"
        #     ),
        #     header=0,
        #     index_col=None,
        # )
        # dataframes_dict["partial_1_df"] = DataFrameParams(
        #     name="partial_1_df", description="", content=df
        # )
        # custom_prefix: str = """
        #     You are an assistant specialized in software development with Python and efficiently data processing using Pandas library.
        #     You have access to the following pandas DataFrames to perform your activities:

        #         {dataframes_descriptions}
        #     """
        # dataframes_list = []
        # sorted_items = sorted(
        #     {
        #         1: "partial_1_df",
        #         2: "apprentice_employee_df",
        #         3: "intern_employee_df",
        #     }.items()
        # )
        # for key, value in sorted_items:
        #     df_params = dataframes_dict[value]
        #     dataframes_list.append(
        #         f"{key}. df{key} ({df_params.name})"
        #         if key == 1
        #         else f"                {key}. df{key} ({df_params.name})"
        #     )
        # formatted_custom_prefix: str = custom_prefix.format(
        #     dataframes_descriptions="\n".join(dataframes_list),
        # )
        # logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")

        # custom_suffix = """
        #     Critical rules:
        #     - Execute all steps provided in the prompt in the correct order.
        #     - Do not ask for confirmation or provide intermediate results.
        #     - Once all steps are complete, save the `resulting` DataFrame to a CSV file and return the final answer.
        #     """
        # logger.info(f"custom_suffix:\n{custom_suffix}")

        # input: str = """
        #     Your task is to process data and save the `resulting` DataFrame to a CSV file.

        #     To do this, perform the following steps in order:

        #     1. From the `df1` (df_partial_1) and `df2` (apprentice_employee_df) DataFrames:
        #     - Rename the `employee_id_apprentice_employee_df` column of the `df2` DataFrame to `employee_id`.
        #     - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
        #     - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

        #     2. From the `resulting` and `df3` (intern_employee_df) DataFrames:
        #     - Rename the `employee_id_intern_employee_df` column of the `df3` DataFrame to `employee_id`.
        #     - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
        #     - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

        #     3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
        #     """
        # formatted_input: str = input.format(
        #     output_path=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_2.csv"
        #     ),
        # )
        # logger.info(f"formatted_input: {formatted_input}")

        # assistant = create_pandas_dataframe_agent(
        #     llm=llm.chat_model,
        #     df=[dataframes_dict[value].content for _, value in sorted_items],
        #     agent_type=AgentType.OPENAI_FUNCTIONS,
        #     allow_dangerous_code=True,
        #     prefix=formatted_custom_prefix,
        #     suffix=custom_suffix,
        #     verbose=True,
        # )

        # result = assistant.invoke({"input": formatted_input})
        # logger.info(f"result: {result}")

        # # Part 3
        # # ------------------------------------------------------------------------------
        # df = pd.read_csv(
        #     filepath_or_buffer=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_2.csv"
        #     ),
        #     header=0,
        #     index_col=None,
        # )
        # dataframes_dict["partial_2_df"] = DataFrameParams(
        #     name="partial_2_df", description="", content=df
        # )
        # custom_prefix: str = """
        #     You are an assistant specialized in software development with Python and efficiently data processing using Pandas library.
        #     You have access to the following pandas DataFrames to perform your activities:

        #         {dataframes_descriptions}
        #     """
        # dataframes_list = []
        # sorted_items = sorted(
        #     {
        #         1: "partial_2_df",
        #         2: "employee_abroad_df",
        #         3: "employee_vacation_df",
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
        #     - Once all steps are complete, save the `resulting` DataFrame to a CSV file and return the final answer.
        #     """
        # logger.info(f"custom_suffix:\n{custom_suffix}")

        # input: str = """
        #     Your task is to process data and save the `resulting` DataFrame to a CSV file.

        #     To do this, perform the following steps in order:

        #     1. From the `df1` (partial_2_df) and `df2` (employee_abroad_df) DataFrames:
        #     - Rename the `register_employee_abroad_df` column of the `df2` DataFrame to `employee_id`.
        #     - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
        #     - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

        #     2. From the `resulting` and `df3` (employee_vacation_df) DataFrames:
        #     - Rename the `employee_id_employee_vacation_df` column of the `df3` DataFrame to `employee_id`.
        #     - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
        #     - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

        #     3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
        #     """
        # formatted_input: str = input.format(
        #     output_path=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_3.csv"
        #     ),
        # )
        # logger.info(f"formatted_input: {formatted_input}")

        # assistant = create_pandas_dataframe_agent(
        #     llm=llm.chat_model,
        #     df=[dataframes_dict[value].content for _, value in sorted_items],
        #     agent_type=AgentType.OPENAI_FUNCTIONS,
        #     allow_dangerous_code=True,
        #     prefix=formatted_custom_prefix,
        #     suffix=custom_suffix,
        #     verbose=True,
        # )

        # result = assistant.invoke({"input": formatted_input})
        # logger.info(f"result: {result}")

        # Part 4
        # ------------------------------------------------------------------------------
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_3.csv"
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["partial_3_df"] = DataFrameParams(
            name="partial_3_df", description="", content=df
        )

        extract_absense_return_date_tool = ExtractAbsenseReturnDateTool()

        def extract_absense_return_date_helper(date_str: str):
            tool_output = extract_absense_return_date_tool._run(date_str)

            if tool_output.status == Status.SUCCEED:
                return tool_output.result
            else:
                return None

        employee_absense_df = dataframes_dict["employee_absense_df"].content

        employee_absense_df["return_date_employee_absense_df"] = employee_absense_df[
            "detail_employee_absense_df"
        ].apply(extract_absense_return_date_helper)

        WORKING_DAYS_OF_MAY = [
            2,
            5,
            6,
            7,
            8,
            9,
            12,
            13,
            14,
            15,
            16,
            19,
            20,
            21,
            22,
            23,
            26,
            27,
            28,
            29,
            30,
        ]
        MAY = 5
        calculate_absense_tool = CalculateAbsenseDaysTool()

        def absense_days_helper(row):
            date_str = row["return_date_employee_absense_df"]

            tool_output = calculate_absense_tool._run(
                date_str, WORKING_DAYS_OF_MAY, MAY
            )

            if tool_output.status == Status.SUCCEED:
                return tool_output.result
            else:
                return None

        employee_absense_df["absense_days_employee_absense_df"] = (
            employee_absense_df.apply(absense_days_helper, axis=1)
        )

        dataframes_dict["employee_absense_df"].content = employee_absense_df

        custom_prefix: str = """
            You are an assistant specialized in software development with Python and efficiently data processing using Pandas library.
            You have access to the following pandas DataFrames to perform your activities:

                {dataframes_descriptions}
            """
        dataframes_list = []
        sorted_items = sorted(
            {
                1: "partial_3_df",
                2: "employee_absense_df",
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
            - Once all steps are complete, save the `resulting` DataFrame to a CSV file and return the final answer.
            """
        logger.info(f"custom_suffix:\n{custom_suffix}")

        input: str = """
            Your task is to process data and save the `resulting` DataFrame to a CSV file.

            To do this, perform the following steps in order:

            1. From the `df1` (partial_3_df) and `df2` (employee_absense_df) DataFrames:
            - Rename the `employee_id_employee_absense_df` column of the `df2` DataFrame to `employee_id`.
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column.
            - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them.

            2. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_4.csv"
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")

        assistant: AgentExecutor = create_pandas_dataframe_agent(
            llm=llm.chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )

        result = assistant.invoke({"input": formatted_input})
        logger.info(f"result: {result}")

        # Part 5
        # ------------------------------------------------------------------------------
        # df = pd.read_csv(
        #     filepath_or_buffer=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_4.csv"
        #     ),
        #     header=0,
        #     index_col=None,
        # )
        # dataframes_dict["partial_4_df"] = DataFrameParams(
        #     name="partial_4_df", description="", content=df
        # )
        # custom_prefix: str = """
        #     You are an assistant specialized in software development with Python and efficiently data processing using Pandas library.
        #     You have access to the following pandas DataFrames to perform your activities:

        #         {dataframes_descriptions}
        #     """
        # dataframes_list = []
        # sorted_items = sorted(
        #     {
        #         1: "partial_4_df",
        #         2: "syndicate_working_days_df",
        #         3: "syndicate_meal_voucher_value_df",
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
        #     - Once all steps are complete, save the `resulting` DataFrame to a CSV file and return the final answer.
        #     """
        # logger.info(f"custom_suffix:\n{custom_suffix}")

        # STATE_MAPPING = {
        #     "AC": "Acre",
        #     "AL": "Alagoas",
        #     "AP": "Amapá",
        #     "AM": "Amazonas",
        #     "BA": "Bahia",
        #     "CE": "Ceará",
        #     "DF": "Distrito Federal",
        #     "ES": "Espírito Santo",
        #     "GO": "Goiás",
        #     "MA": "Maranhão",
        #     "MT": "Mato Grosso",
        #     "MS": "Mato Grosso do Sul",
        #     "MG": "Minas Gerais",
        #     "PA": "Pará",
        #     "PB": "Paraíba",
        #     "PR": "Paraná",
        #     "PE": "Pernambuco",
        #     "PI": "Piauí",
        #     "RJ": "Rio de Janeiro",
        #     "RN": "Rio Grande do Norte",
        #     "RS": "Rio Grande do Sul",
        #     "RO": "Rondônia",
        #     "RR": "Roraima",
        #     "SC": "Santa Catarina",
        #     "SP": "São Paulo",
        #     "SE": "Sergipe",
        #     "TO": "Tocantins",
        # }

        # input: str = """
        #     Your task is to process data and save the `resulting` DataFrame to a CSV file.

        #     To do this, perform the following steps in order:

        #     1. From the `df2` (syndicate_working_days_df) and `df3` (syndicate_meal_voucher_value_df) DataFrames:
        #     - Identity the two-letter state code from the `name_syndicate_working_days_df` column in `df2` DataFrame (e.g., extract 'PR' from 'SITEPD PR - ...'). Assume the state code is a two-letter code separated by spaces or other delimiters.
        #     - Add a new column `state_code_syndicate_working_days_df` to `df2` DataFrame with the extracted state code.
        #     - Use the following mapping of Brazilian state codes to state names:
        #         {state_mapping}
        #     - Add a new column `state_name_syndicate_working_days_df` to `df2` DataFrame by mapping the `state_code_syndicate_working_days_df` to the full state name using the provided state mapping.
        #     - Merge `df2` DataFrame with `df3` DataFrame on thew `state_name_syndicate_working_days_df` (from `df2`) and `state_syndicate_meal_voucher_value_df` (from `df3`) columns using an inner join to keep only matching rows.

        #     2. From the `df1` (partial_4_df) and `resulting` DataFrames:
        #     - Rename the `syndicate_name_active_employee_df` column of the `df1` DataFrame to `syndicate_name`.
        #     - Rename the `name_syndicate_working_days_df` column of the `resulting` DataFrame to `syndicate_name`.
        #     - Perform LEFT merge operation with `df1` and `resulting` DataFrames on `syndicate_name` column;

        #     3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
        #     """
        # formatted_input: str = input.format(
        #     state_mapping=STATE_MAPPING,
        #     output_path=os.path.join(
        #         app_settings.output_data_dir_path, "VR MENSAL 05.2025_partial_5.csv"
        #     ),
        # )
        # logger.info(f"formatted_input: {formatted_input}")

        # assistant = create_pandas_dataframe_agent(
        #     llm=llm.chat_model,
        #     df=[dataframes_dict[value].content for _, value in sorted_items],
        #     agent_type=AgentType.OPENAI_FUNCTIONS,
        #     allow_dangerous_code=True,
        #     prefix=formatted_custom_prefix,
        #     suffix=custom_suffix,
        #     verbose=True,
        # )

        # result = assistant.invoke({"input": formatted_input})
        # logger.info(f"result: {result}")
