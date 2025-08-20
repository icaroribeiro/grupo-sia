import functools
import os

import pandas as pd
from src.layers.business_layer.ai_agents.tools.top_level_handoff_tool import (
    TopLevelHandoffTool,
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


class TopLevelWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        extract_absense_return_date_tool: ExtractAbsenseReturnDateTool,
        calculate_absense_days_tool: CalculateAbsenseDaysTool,
    ):
        self.name = "top_level_workflow"
        self.chat_model = chat_model
        self.dataframes_dict = dataframes_dict
        self.extract_absense_return_date_tool = extract_absense_return_date_tool
        self.calculate_absense_days_tool = calculate_absense_days_tool
        self.__agent_custom_prefix: str = """
            ROLE:
            - You are an agent specialized in software development with Python and efficiently data processing using Pandas library.
            GOAL:
            - Your sole purpose is to process data and save the `resulting` DataFrame to a CSV file.
            - To do this, you have access to the following pandas DataFrames:

                {dataframes_descriptions}
            """
        self.__agent_custom_suffix = """
            CRITICAL RULES:
            - Execute all steps provided in the prompt in the correct order.
            - Do not ask for confirmation or provide intermediate results.
            - Once all steps are complete, save the `resulting` DataFrame to a CSV file and return the final answer.
            """
        delegate_to_data_gathering_agent = TopLevelHandoffTool(
            agent_name="data_gathering_agent"
        )
        delegate_to_data_analysis_agent = TopLevelHandoffTool(
            agent_name="data_analysis_agent"
        )
        delegate_to_data_reporting_agent = TopLevelHandoffTool(
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
        self.__graph = self._build_graph()

    @staticmethod
    def __call_data_gathering_agent(
        state: StateGraph,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        extract_absense_return_date_tool: ExtractAbsenseReturnDateTool,
        calculate_absense_days_tool: CalculateAbsenseDaysTool,
        custom_prefix: str,
        custom_suffix: str,
    ) -> StateGraph:
        dataframes_list = []
        sorted_items = sorted(
            {
                1: "active_employee_df",
                2: "employee_admission_df",
                3: "employee_dismissal_df",
            }.items()
        )
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key}. df{key} ({df_params.name})"
                if key == 1
                else f"                {key}. df{key} ({df_params.name})"
            )
        formatted_custom_prefix: str = custom_prefix.format(
            dataframes_descriptions="\n".join(dataframes_list),
        )

        input: str = """
            INSTRUCTIONS:
            - Perform the following steps in order:

            1. From the `df1` (active_employee_df) and `df2` (employee_admission_df) DataFrames:
            - Rename the `employee_id_active_employee_df` column of the `df1` DataFrame to `employee_id`.
            - Rename the `employee_id_employee_admission_df` column of the `df2` DataFrame to `employee_id`.
            - Perform LEFT merge operation with `df1` and `df2` DataFrames on `employee_id` column;
            - If there are rows in the `df2` DataFrame not included in `df1` DataFrame based on `employee_id` column, concatenate them;

            2. From the `resulting` and `df3` (employee_dismissal_df) DataFrames:
            - Rename the `employee_id_employee_dismissal_df` column of the `df1` DataFrame to `employee_id`.
            - Perform LEFT merge operation with `resulting` and `df3` DataFrames on `employee_id` column;
            - If there are rows in the `df3` DataFrame not included in `resulting` DataFrame based on `employee_id` column, concatenate them;

            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}/tmp/",
                "VR MENSAL 05.2025_partial_5.csv",
            ),
        )

        agent = create_pandas_dataframe_agent(
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
    def __call_data_analysis_agent(
        state: StateGraph,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        custom_prefix: str,
        custom_suffix: str,
    ) -> StateGraph:
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}/tmp/",
                "VR MENSAL 05.2025_partial_5.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["partial_5_df"] = DataFrameParams(
            name="partial_5_df", description="", content=df
        )

        dataframes_list = []
        sorted_items = sorted(
            {
                1: "partial_5_df",
            }.items()
        )
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key}. df{key} ({df_params.name})"
                if key == 1
                else f"                {key}. df{key} ({df_params.name})"
            )
        formatted_custom_prefix: str = custom_prefix.format(
            dataframes_descriptions="\n".join(dataframes_list),
        )

        input: str = """
            INSTRUCTIONS:
            Perform the following steps in order:

            1. From the `df1` (partial_df_5) DataFrame:
            - Rename the `company_id_active_employee_df` column of the `df1` DataFrame to `company_id_changed_by_data_analysis_agent`.

            2. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}/tmp/",
                "VR MENSAL 05.2025_partial_6.csv",
            ),
        )

        agent = create_pandas_dataframe_agent(
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
    def __call_data_reporting_agent(
        state: StateGraph,
        chat_model: BaseChatModel,
        dataframes_dict: dict[str, DataFrameParams],
        custom_prefix: str,
        custom_suffix: str,
    ) -> StateGraph:
        df = pd.read_csv(
            filepath_or_buffer=os.path.join(
                f"{app_settings.output_data_dir_path}/tmp/",
                "VR MENSAL 05.2025_partial_6.csv",
            ),
            header=0,
            index_col=None,
        )
        dataframes_dict["partial_6_df"] = DataFrameParams(
            name="partial_6_df", description="", content=df
        )

        dataframes_list = []
        sorted_items = sorted(
            {
                1: "partial_6_df",
            }.items()
        )
        for key, value in sorted_items:
            df_params = dataframes_dict[value]
            dataframes_list.append(
                f"{key}. df{key} ({df_params.name})"
                if key == 1
                else f"                {key}. df{key} ({df_params.name})"
            )
        formatted_custom_prefix: str = custom_prefix.format(
            dataframes_descriptions="\n".join(dataframes_list),
        )

        input: str = """
            INSTRUCTIONS:
            - Perform the following steps in order:

            1. From the `df1` (partial_df_6) DataFrame:
            - Rename the `employee_id` column of the `df1` DataFrame to `Matricula`.
            - Rename the `admission_date_employee_admission_df` column of the `df1` DataFrame to `Admissão`.
            - Rename the `syndicate_name` column of the `df1` DataFrame to `Sindicato do Colaborador`.
            - Add a new column named `Competência` and fill out the rows with value `01/05/2025`.

            2. From the `resulting` DataFrame:
            - Change the order of the columns as below:
                1. `Matricula`
                2. `Admissão`
                3. `Sindicato do Colaborador`
                4. `Competência`
                5. The others can be kept as they are.

            3. Save the `resulting` DataFrame to a CSV file to the path `{output_path}`.
            """
        formatted_input: str = input.format(
            output_path=os.path.join(
                f"{app_settings.output_data_dir_path}",
                "VR MENSAL 05.2025_FINAL.csv",
            ),
        )

        agent = create_pandas_dataframe_agent(
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

    def _build_graph(self) -> StateGraph:
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
