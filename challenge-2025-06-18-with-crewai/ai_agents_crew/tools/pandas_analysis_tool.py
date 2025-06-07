import io
from typing import Dict

import pandas as pd
from crewai.tools import BaseTool
from ai_agents_crew.logger.logger import logger
from abc import ABC, abstractmethod


class BaseDataFrameTool(BaseTool, ABC):
    dataframes_dict: Dict = dict()

    def __init__(self, dataframes_dict: Dict):
        super().__init__()
        self.dataframes_dict = dataframes_dict

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        pass


class GetDataFrameHeadTool(BaseDataFrameTool):
    name: str = "Get DataFrame Head"
    description: str = """
        Returns the head (first n rows) of a specified DataFrame.
        Use filename as key to identify the DataFrame (e.g., '202401_NFs_Cabecalho.csv').

        Arguments:
            dataframe_key (str): The key to identiry the DataFrame.
            n (int): The number of DataFrame rows to display.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, n: int = 5) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        df = self.dataframes_dict[dataframe_key]
        return f"Head of '{dataframe_key}':\n{df.head(n).to_markdown(index=False)}"


class GetDataFrameInfoTool(BaseDataFrameTool):
    name: str = "Get DataFrame Info"
    description: str = """
        Returns concise summary of a DataFrame, including data types and non-null values.
        Use dataframe_key to identify the DataFrame.

        Arguments:
            dataframe_key (str): The key to identiry the DataFrame.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        df = self.dataframes_dict[dataframe_key]
        buf = io.StringIO()
        df.info(buf=buf)
        return f"Info for '{dataframe_key}':\n{buf.getvalue()}"


if __name__ == "__main__":
    logger.info("Starting Pandas analysis tool...")
    df1 = pd.DataFrame(
        {
            "CHAVE DE ACESSO": [
                41240106267630001509550010035101291224888487,
                50240129843878000170550010000025251000181553,
                50240112977901000117550010000051831659469117,
            ]
        }
    )
    dataframes_dict = {"202401_NFs_Cabecalho.csv": df1}
    get_dataframe_head_tool_result = GetDataFrameHeadTool(
        dataframes_dict=dataframes_dict
    )._run(dataframe_key="202401_NFs_Cabecalho.csv", n=2)
    logger.info(f"Get DataFrame Head tool result: {get_dataframe_head_tool_result}")
    get_dataframe_info_tool_result = GetDataFrameInfoTool(
        dataframes_dict=dataframes_dict
    )._run(dataframe_key="202401_NFs_Cabecalho.csv")
    logger.info(f"Get DataFrame Info tool result: {get_dataframe_info_tool_result}")
    logger.info("Pandas analysis tool successfully executed!")
