import functools
import os
from langchain.agents import AgentExecutor
import pandas as pd
from src.layers.business_layer.ai_agents.models.tool_output import Status
from src.layers.business_layer.ai_agents.tools.meal_voucher_handoff_tool import (
    MealVoucherHandoffTool,
)
from src.layers.data_access_layer.pandas.models.dataframe_params import DataFrameParams
from src.layers.business_layer.ai_agents.tools.calculate_absense_days_tool import (
    CalculateAbsenseDaysTool,
)
from src.layers.business_layer.ai_agents.tools.extract_absense_return_date_tool import (
    ExtractAbsenseReturnDateTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, MessagesState, START
import uuid
from langchain_core.messages import HumanMessage

from src.layers.core_logic_layer.settings import app_settings

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType


class MealVoucherWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        extract_absense_return_date_tool: ExtractAbsenseReturnDateTool,
        calculate_absense_days_tool: CalculateAbsenseDaysTool,
    ):
        self.name = "meal_voucher_workflow"
        self.chat_model = chat_model
        self.dataframes_dict = dataframes_dict
        self.extract_absense_return_date_tool = extract_absense_return_date_tool
        self.calculate_absense_days_tool = calculate_absense_days_tool
        self.__agent_custom_prefix: str = """
            ROLE:
            - You are an agent specialized in software development with Python and efficiently data processing using Pandas library.
            GOAL:
            - Your sole purpose is to process data and save the `resulting` DataFrame to a specific file.
            - To do this, you have access to the following pandas DataFrames:

                {dataframes_descriptions}
            """
        self.__agent_custom_suffix = """
            CRITICAL RULES:
            - Do not ask for confirmation or provide intermediate results.
            - Execute all steps provided in the prompt in the correct order.
            """
        delegate_to_data_gathering_agent = MealVoucherHandoffTool(
            agent_name="data_gathering_agent"
        )
        delegate_to_data_analysis_agent = MealVoucherHandoffTool(
            agent_name="data_analysis_agent"
        )
        delegate_to_data_reporting_agent = MealVoucherHandoffTool(
            agent_name="data_reporting_agent"
        )
        self.supervisor = create_react_agent(
            model=self.chat_model,
            tools=[
                delegate_to_data_gathering_agent,
                delegate_to_data_analysis_agent,
                delegate_to_data_reporting_agent,
            ],
            prompt=(
                """
                ROLE:
                - You're a supervisor.
                GOAL:
                - Your sole purpose is to manage three agents:
                A data gathering agent. Assign data gathering-related tasks to this agent.
                A data analysis agent. Assign data analysis-related tasks to this agent.
                A data reporting agent. Assign data reporting-related tasks to this agent.
                INSTRUCTIONS:
                - Based on the conversation history, decide the next step.
                - DO NOT do any work yourself.
                CRITICAL RULES:
                - ALWAYS assign work to one agent at a time, DO NOT call agents in parallel.
                """
            ),
            name="supervisor",
        )
        self.__graph = self.__build_graph()

    def __call_data_gathering_agent(
        self,
        state: StateGraph,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        extract_absense_return_date_tool: ExtractAbsenseReturnDateTool,
        calculate_absense_days_tool: CalculateAbsenseDaysTool,
        custom_prefix: str,
        custom_suffix: str,
    ) -> StateGraph:
        all_results = []
        sorted_items = sorted(
            {
                1: "df_active_employee",
                2: "df_employee_admission",
                3: "df_employee_dismissal",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        input: str = """
            INSTRUCTIONS:
            - Perform the following steps in order:

            1. From the `df1` (df_active_employee) and `df2` (df_employee_admission) DataFrames:
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
            - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

            2. From the `resulting` and `df3` (df_employee_dismissal) DataFrames:
            - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
            - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_1.csv",
            ),
        )
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_1.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_gathering_result_1"] = DataFrameParams(
            name="df_partial_gathering_result_1", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_gathering_result_1",
                2: "df_apprentice_employee",
                3: "df_intern_employee",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")
        input: str = """
            Your task is to process data and save the `resulting` DataFrame to a CSV file.

            To do this, perform the following steps in order:

            1. From the `df1` (df_partial_gathering_result_1) and `df2` (df_apprentice_employee) DataFrames:
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
            - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

            2. From the `resulting` and `df3` (df_intern_employee) DataFrames:
            - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
            - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_2.csv",
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_2.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_gathering_result_2"] = DataFrameParams(
            name="df_partial_gathering_result_2", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_gathering_result_2",
                2: "df_employee_abroad",
                3: "df_employee_vacation",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")
        input: str = """
            Your task is to process data and save the `resulting` DataFrame to a CSV file.

            To do this, perform the following steps in order:

            1. From the `df1` (df_partial_gathering_result_2) and `df2` (df_employee_abroad) DataFrames:
            - Rename the `register` column of the `df2` DataFrame to `employee_id`.
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
            - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

            2. From the `resulting` and `df3` (df_employee_vacation) DataFrames:
            - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
            - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_3.csv",
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_3.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_gathering_result_3"] = DataFrameParams(
            name="df_partial_gathering_result_3", content=df
        )
        sorted_items = sorted(
            {
                1: "df_syndicate_working_days",
                2: "df_syndicate_meal_voucher_value",
                3: "df_partial_gathering_result_3",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        STATE_MAPPING = {
            "AC": "Acre",
            "AL": "Alagoas",
            "AP": "Amapá",
            "AM": "Amazonas",
            "BA": "Bahia",
            "CE": "Ceará",
            "DF": "Distrito Federal",
            "ES": "Espírito Santo",
            "GO": "Goiás",
            "MA": "Maranhão",
            "MT": "Mato Grosso",
            "MS": "Mato Grosso do Sul",
            "MG": "Minas Gerais",
            "PA": "Pará",
            "PB": "Paraíba",
            "PR": "Paraná",
            "PE": "Pernambuco",
            "PI": "Piauí",
            "RJ": "Rio de Janeiro",
            "RN": "Rio Grande do Norte",
            "RS": "Rio Grande do Sul",
            "RO": "Rondônia",
            "RR": "Roraima",
            "SC": "Santa Catarina",
            "SP": "São Paulo",
            "SE": "Sergipe",
            "TO": "Tocantins",
        }
        input: str = """
            Your task is to process data and save the `resulting` DataFrame to a CSV file.

            To do this, perform the following steps in order:

            1. From the `df1` (df_syndicate_working_days) and `df2` (df_syndicate_meal_voucher_value) DataFrames:
            - Identity the two-letter state code from the `name` column in `df1` DataFrame (e.g., extract 'PR' from 'SITEPD PR - ...'). Assume the state code is a two-letter code separated by spaces or other delimiters.
            - Add a new column `state_code` to `df1` DataFrame with the extracted state code.
            - Use the following mapping of Brazilian state codes to state names:
                {state_mapping}
            - Add a new column `state_name` to `df1` DataFrame by mapping the `state_code` to the full state name using the provided state mapping.
            - Rename the `state` column of the `df2` DataFrame to `state_name`.
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `state_name` column;

            2. From the `df3` (df_partial_gathering_result_3) and `resulting` DataFrames:
            - Rename the `name` column of the `resulting` DataFrame to `syndicate_name`.
            - Perform LEFT merge operation with `df3` and `resulting` DataFrames on `syndicate_name` column;

            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            state_mapping=STATE_MAPPING,
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_4.csv",
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)

        def extract_absense_return_date_helper(date_str: str):
            tool_output = extract_absense_return_date_tool._run(date_str)

            if tool_output.status == Status.SUCCEED:
                return tool_output.result
            else:
                return None

        df_employee_absense = dataframes_dict["df_employee_absense"].content
        df_employee_absense["return_date"] = df_employee_absense["detail"].apply(
            extract_absense_return_date_helper
        )
        dataframes_dict["df_employee_absense"].content = df_employee_absense
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_4.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_gathering_result_4"] = DataFrameParams(
            name="df_partial_gathering_result_4", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_gathering_result_4",
                2: "df_employee_absense",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")
        input: str = """
            Your task is to process data and save the `resulting` DataFrame to a CSV file.

            To do this, perform the following steps in order:

            1. From the `df1` (df_partial_gathering_result_4) and `df2` (df_employee_absense) DataFrames:
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column.
            - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them.

            2. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_5.csv",
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_5.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_gathering_result_5"] = DataFrameParams(
            name="df_partial_gathering_result_5", content=df
        )
        working_days_by_syndicate_name = {
            "SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS DE CURITIBA E REGIAO METROPOLITANA": {
                5: [
                    1,
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
                ],
            },
            "SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL": {
                5: [
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
            },
            "SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.": {
                5: [
                    1,
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
            },
            "SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS DO RIO DE JANEIRO": {
                5: [
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
                ],
            },
        }

        def absense_days_helper(row):
            date_str = row["return_date"]
            syndicate_name = row["syndicate_name"]

            tool_output = calculate_absense_days_tool._run(
                date_str=date_str,
                working_days_by_syndicate_name=working_days_by_syndicate_name,
                syndicate_name=syndicate_name,
            )

            if tool_output.status == Status.SUCCEED:
                return tool_output.result
            else:
                return None

        df_partial_gathering_result_5 = dataframes_dict[
            "df_partial_gathering_result_5"
        ].content
        df_partial_gathering_result_5["absense_days"] = (
            df_partial_gathering_result_5.apply(absense_days_helper, axis=1)
        )
        dataframes_dict[
            "df_partial_gathering_result_5"
        ].content = df_partial_gathering_result_5
        sorted_items = sorted(
            {
                1: "df_partial_gathering_result_5",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        logger.info(f"formatted_custom_prefix:\n{formatted_custom_prefix}")
        input: str = """
            Your task is to process data and save the `resulting` DataFrame to a CSV file.

            To do this, perform the following steps in order:

            1. Save the `df1` (df_partial_gathering_result_5) DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_6.csv",
            ),
        )
        logger.info(f"formatted_input: {formatted_input}")
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        # Extract the 'output' key from each result dictionary and join them with a separator.
        final_content = "\n\n---\nAgent Step Finished\n---\n\n".join(
            [str(res.get("output", "No output returned.")) for res in all_results]
        )
        return {"messages": [HumanMessage(content=final_content)]}

    def __call_data_analysis_agent(
        self,
        state: StateGraph,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        custom_prefix: str,
        custom_suffix: str,
    ) -> StateGraph:
        all_results = []
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_gathering_result_6.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_gathering_result_6"] = DataFrameParams(
            name="df_partial_gathering_result_6", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_gathering_result_6",
                2: "df_employee_absense",
                3: "df_employee_abroad",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        input: str = """
            INSTRUCTIONS:
            Perform the following steps in order:

            1. From the `df1` (df_partial_gathering_result_6) DataFrame:
            - Filter out rows in `df1` DataFrame where any column starting with `job_title` contains the substrings `DIRETOR`, `ESTAGIARIO`, or `APRENDIZ` (case-sensitive).

            3. From the `resulting` and `df2` (df_employee_absense) DataFrames:
            - Filter out rows in `resulting` DataFrame where the value in `employee_id` column is the same value in `employee_id` column from `df2` DataFrame AND the date in `return_date` is not missing and did not occur in May month.

            3. From the `resulting` and `df3` (df_employee_abroad) DataFrames:
            - Filter out rows in `resulting` DataFrame where the value in `employee_id` column is the same value in `register` column from `df3` DataFrame.
            
            4. From the `resulting` DataFrame:
            - Filter out rows in `resulting` DataFrame where the value in `syndicate_name` column is missing.

            5. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_analysis_result_1.csv",
            ),
        )
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_analysis_result_1.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_analysis_result_1"] = DataFrameParams(
            name="df_partial_analysis_result_1", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_analysis_result_1",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        input: str = """
            INSTRUCTIONS:
            Perform the following steps in order:

            1. From the `df1` (df_partial_analysis_result_1) DataFrame:
            - For each row, remove the row if the value in `termination_notice` is `OK` AND the date in `termination_date` occurs on or before the 15th of the month.

            2. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_analysis_result_2.csv",
            ),
        )
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_analysis_result_2.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_analysis_result_2"] = DataFrameParams(
            name="df_partial_analysis_result_2", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_analysis_result_2",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        input: str = """
            INSTRUCTIONS:
            Perform the following steps in order:

            1. From the `df1` (df_partial_analysis_result_2) DataFrame:
            - Add a new column named `effective_working_days` and fill out the rows with the value of Formula: 
                - `df1`['effective_working_days'] = `df1`['working_days'] - `df1`['vacation_days'] - `df1`['absense_days']
                - For each row, handle missing values for `absense_days` and `vacation_days` by setting them to 0.
            - Add a new column named `daily_meal_voucher_value` and fill out the rows with the same as the value in the existing `meal_voucher_value` column.
            - Add a new column named `total_meal_voucher_value` and fill out the rows with the value of Formula: 
                - `df1`['total_meal_voucher_value'] = `df1`['effective_working_days`] * `df1`['daily_meal_voucher_value']
            - Add a new column named `company_meal_voucher_cost` and fill out the rows with the value of Formula: 
                - `df1`['company_meal_voucher_cost'] = `df1`['total_meal_voucher_value'] * 0.80
            - Add a new column named `employee_meal_voucher_discount` and fill out the rows with the value of Formula: 
                - `df1`['employee_meal_voucher_discount'] = `df1`[total_meal_voucher_value'] * 0.20

            2. From the `resulting` DataFrame:
            - Filter out rows in `resulting` DataFrame where the value in `effective_working_days` column is zero or negative.
            
            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_analysis_result_3.csv",
            ),
        )
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        all_results.append(result)
        # Extract the 'output' key from each result dictionary and join them with a separator.
        final_content = "\n\n---\nAgent Step Finished\n---\n\n".join(
            [str(res.get("output", "No output returned.")) for res in all_results]
        )
        return {"messages": [HumanMessage(content=final_content)]}

    def __call_data_reporting_agent(
        self,
        state: StateGraph,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        custom_prefix: str,
        custom_suffix: str,
    ) -> StateGraph:
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "df_partial_analysis_result_3.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["df_partial_analysis_result_3"] = DataFrameParams(
            name="df_partial_analysis_result_3", content=df
        )
        sorted_items = sorted(
            {
                1: "df_partial_analysis_result_3",
            }.items()
        )
        formatted_custom_prefix: str = self.__create_dataframe_description(
            sorted_items=sorted_items,
            dataframes_dict=dataframes_dict,
            custom_prefix=custom_prefix,
        )
        input: str = """
            INSTRUCTIONS:
            - Perform the following steps in order:

            1. From the `df1` (df_partial_analysis_result_3) DataFrame:
            - Create a new `resulting` Dataframe and copy from `df1` DataFrame only the columns below in order:
                1. `employee_id`
                2. `admission_date`
                3. `syndicate_name`
                4. `effective_working_days`
                5. `daily_meal_voucher_value`
                6. `total_meal_voucher_value`
                7. `company_meal_voucher_cost`
                8. `employee_meal_voucher_discount`

            2. From the `resulting` DataFrame:
            - Rename the `employee_id` column of the `resulting` DataFrame to `Matricula`.
            - Rename the `admission_date` column of the `resulting` DataFrame to `Admissão`.
            - Rename the `syndicate_name` column of the `resulting` DataFrame to `Sindicato do Colaborador`.
            - Rename the `effective_working_days` column of the `resulting` DataFrame to `Dias`.
            - Rename the `daily_meal_voucher_value` column of the `resulting` DataFrame to `VALOR DIÁRIO VR`.
            - Rename the `total_meal_voucher_value` column of the `resulting` DataFrame to `TOTAL`.
            - Rename the `company_meal_voucher_cost` column of the `resulting` DataFrame to `Custo empresa`.
            - Rename the `employee_meal_voucher_discount` column of the `resulting` DataFrame to `Desconto profissional`.
            - Add a new column named `Competência` and fill out the rows with value `01/05/2025`.

            3. From the `resulting` DataFrame:
            - Change the order of the columns as below:
                1. `Matricula`
                2. `Admissão`
                3. `Sindicato do Colaborador`
                4. `Competência`
                5. `Dias`
                6. `VALOR DIÁRIO VR`
                7. `TOTAL`
                8. `Custo empresa`
                9. `Desconto profissional`

            4. Save the `resulting` DataFrame to a CSV file to the path `{output_csv_file_path}`.

            5. Save the `resulting` DataFrame to a XLSX file to the path `{output_xlsx_file_path}`.
            """
        formatted_input: str = input.format(
            output_csv_file_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "VR MENSAL 05.2025.csv",
            ),
            output_xlsx_file_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "VR MENSAL 05.2025.xlsx",
            ),
        )
        agent: AgentExecutor = create_pandas_dataframe_agent(
            llm=chat_model,
            df=[dataframes_dict[value].content for _, value in sorted_items],
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=formatted_custom_prefix,
            suffix=custom_suffix,
            verbose=True,
        )
        result = agent.invoke({"input": formatted_input})
        logger.info(f"result: {result}")
        return {"messages": [HumanMessage(content=str(result))]}

    @staticmethod
    def __create_dataframe_description(
        sorted_items: list[tuple[int, str]],
        dataframes_dict: dict[str, "DataFrameParams"],
        custom_prefix: str,
    ) -> str:
        dataframes_list = []
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key}. df{key} ({df_params.name})"
                if key == 1
                else f"                {key}. df{key} ({df_params.name})"
            )
        return custom_prefix.format(dataframes_descriptions="\n".join(dataframes_list))

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)
        builder.add_node(
            node=self.supervisor.name,
            action=self.supervisor,
            destinations={
                "data_gathering_agent": "data_gathering_agent",
                "data_analysis_agent": "data_analysis_agent",
                "data_reporting_agent": "data_reporting_agent",
            },
        )
        builder.add_node(
            node="data_gathering_agent",
            action=functools.partial(
                self.__call_data_gathering_agent,
                chat_model=self.chat_model,
                dataframes_dict=self.dataframes_dict,
                extract_absense_return_date_tool=self.extract_absense_return_date_tool,
                calculate_absense_days_tool=self.calculate_absense_days_tool,
                custom_prefix=self.__agent_custom_prefix,
                custom_suffix=self.__agent_custom_suffix,
            ),
        )
        builder.add_node(
            node="data_analysis_agent",
            action=functools.partial(
                self.__call_data_analysis_agent,
                chat_model=self.chat_model,
                dataframes_dict=self.dataframes_dict,
                custom_prefix=self.__agent_custom_prefix,
                custom_suffix=self.__agent_custom_suffix,
            ),
        )
        builder.add_node(
            node="data_reporting_agent",
            action=functools.partial(
                self.__call_data_reporting_agent,
                chat_model=self.chat_model,
                dataframes_dict=self.dataframes_dict,
                custom_prefix=self.__agent_custom_prefix,
                custom_suffix=self.__agent_custom_suffix,
            ),
        )
        builder.add_edge(START, self.supervisor.name)
        builder.add_edge("data_gathering_agent", self.supervisor.name)
        builder.add_edge("data_analysis_agent", self.supervisor.name)
        builder.add_edge("data_reporting_agent", self.supervisor.name)
        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(self, input_message: str) -> dict:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

        async for chunk in self.__graph.astream(
            input_state,
            subgraphs=True,
            config={"configurable": {"thread_id": thread_id}},
        ):
            self._pretty_print_messages(chunk, last_message=True)
        result = chunk[1]["supervisor"]["messages"]
        # for message in result:
        #     message.pretty_print()
        # result = await self.__graph.ainvoke(
        #     input_state,
        #     config={"configurable": {"thread_id": thread_id}},
        # )
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result
