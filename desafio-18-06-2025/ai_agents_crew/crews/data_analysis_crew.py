from typing import Dict

import pandas as pd
from crewai import LLM, Crew, Process

from ai_agents_crew.agents.data_analyst_agent import DataAnalystAgent
from ai_agents_crew.tasks.analyze_data_task import AnalyzeDataTask
from ai_agents_crew.tools.pandas_analysis_tool import (
    CalculateMaxTool,
    CalculateMeanTool,
    CalculateMinTool,
    CountDistinctRowsTool,
    FilterDataFrameTool,
    GetDataFrameHeadTool,
    GetDataFrameInfoTool,
)


class DataAnalysisCrew:
    def __init__(self, llm: LLM):
        self.__llm = llm

    def kickoff_crew(
        self,
        user_query: str,
        dataframes_dict: Dict[str, pd.DataFrame],
    ) -> Crew:
        dataframe_tools = [
            GetDataFrameHeadTool(dataframes_dict=dataframes_dict),
            GetDataFrameInfoTool(dataframes_dict=dataframes_dict),
            FilterDataFrameTool(dataframes_dict=dataframes_dict),
            CalculateMinTool(dataframes_dict=dataframes_dict),
            CalculateMaxTool(dataframes_dict=dataframes_dict),
            CalculateMeanTool(dataframes_dict=dataframes_dict),
            CountDistinctRowsTool(dataframes_dict=dataframes_dict),
        ]

        data_analyst_agent = DataAnalystAgent(llm=self.__llm).create(
            tools=dataframe_tools
        )

        dataframe_keys = list(dataframes_dict.keys())
        available_dataframes_str = ", ".join(dataframe_keys)

        analyze_data_task = AnalyzeDataTask().create(
            user_query=user_query,
            available_dataframes_str=available_dataframes_str,
            agent=data_analyst_agent,
        )

        crew = Crew(
            agents=[data_analyst_agent],
            tasks=[analyze_data_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew
