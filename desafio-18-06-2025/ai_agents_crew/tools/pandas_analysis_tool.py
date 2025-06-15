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
        Use filename as key to identify the DataFrame.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            n (int): The number of DataFrame rows to display.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, n: int = 10) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        return (
            f"Head of '{dataframe_key}':\n{dataframe.head(n).to_markdown(index=False)}"
        )


class GetDataFrameInfoTool(BaseDataFrameTool):
    name: str = "Get DataFrame Info"
    description: str = """
        Returns concise summary of a DataFrame, including data types and non-null values.
        Use dataframe_key to identify the DataFrame.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        buf = io.StringIO()
        dataframe.info(buf=buf)
        return f"Info for '{dataframe_key}':\n{buf.getvalue()}"


class FilterDataFrameTool(BaseDataFrameTool):
    name: str = "Filter DataFrame"
    description: str = """
        Filters a DataFrame based on a column and a specific value.
        Returns the head of the filtered DataFrame or an error if column/value not found.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            column (str): The DataFrame column name.
            value (str): The value to be filtered. 
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, column: str, value: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if column not in dataframe.columns:
            return f"Error: Column '{column}' not found in DataFrame '{dataframe_key}'."
        try:
            filtered_dataframe = dataframe[
                dataframe[column].astype(str).str.contains(value, case=False, na=False)
            ]
            if filtered_dataframe.empty:
                return f"No matching rows found in '{dataframe_key}' for column '{column}' with value '{value}'."
            return f"Filtered data from '{dataframe_key}':\n{filtered_dataframe.head().to_markdown(index=False)}"
        except Exception as err:
            return f"Error filtering DataFrame '{dataframe_key}': {err}"


class CalculateMaxTool(BaseDataFrameTool):
    name: str = "Calculate Max"
    description: str = """
        Calculates the maximum value of a numeric column in a DataFrame.
        Use dataframe_key to identify the DataFrame.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            column (str): The DataFrame column name.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if column not in dataframe.columns:
            return f"Error: Column '{column}' not found in DataFrame '{dataframe_key}'."

        try:
            max_value = dataframe[column].max()
            return f"Max value of '{column}' in '{dataframe_key}': {max_value:.2f}"
        except TypeError:
            return f"Error: Column '{column}' in '{dataframe_key}' is not numeric. Cannot calculate the maximum value."
        except Exception as err:
            return f"Error calculating max value for '{dataframe_key}': {err}"


class CalculateMinTool(BaseDataFrameTool):
    name: str = "Calculate Min"
    description: str = """
        Calculates the minimum value of a numeric column in a DataFrame.
        Use dataframe_key to identify the DataFrame.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            column (str): The DataFrame column name.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if column not in dataframe.columns:
            return f"Error: Column '{column}' not found in DataFrame '{dataframe_key}'."

        try:
            min_value = dataframe[column].min()
            return f"Min value of '{column}' in '{dataframe_key}': {min_value:.2f}"
        except TypeError:
            return f"Error: Column '{column}' in '{dataframe_key}' is not numeric. Cannot calculate the minimum value."
        except Exception as err:
            return f"Error calculating min value for '{dataframe_key}': {err}"


class CalculateMeanTool(BaseDataFrameTool):
    name: str = "Calculate Mean"
    description: str = """
        Calculates the mean of a numeric column in a DataFrame.
        Use dataframe_key to identify the DataFrame.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            column (str): The DataFrame column name.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if column not in dataframe.columns:
            return f"Error: Column '{column}' not found in DataFrame '{dataframe_key}'."

        try:
            max_value = dataframe[column].max()
            return f"Mean of '{column}' in '{dataframe_key}': {max_value:.2f}"
        except TypeError:
            return f"Error: Column '{column}' in '{dataframe_key}' is not numeric. Cannot calculate mean value."
        except Exception as err:
            return f"Error calculating mean value for '{dataframe_key}': {err}"


if __name__ == "__main__":
    logger.info("Starting Pandas analysis tool...")
    dataframe = pd.DataFrame(
        {
            "CHAVE DE ACESSO": [
                41240106267630001509550010035101291224888487,
                50240129843878000170550010000025251000181553,
                50240112977901000117550010000051831659469117,
            ],
            "VALOR NOTA FISCAL": [522.5, 499.0, 337.5],
        }
    )
    dataframes_dict = {"202401_NFs_Cabecalho.csv": dataframe}

    get_dataframe_head_tool_result = GetDataFrameHeadTool(
        dataframes_dict=dataframes_dict
    )._run(dataframe_key="202401_NFs_Cabecalho.csv", n=10)
    logger.info(f"Get DataFrame Head tool result: {get_dataframe_head_tool_result}")

    get_dataframe_info_tool_result = GetDataFrameInfoTool(
        dataframes_dict=dataframes_dict
    )._run(dataframe_key="202401_NFs_Cabecalho.csv")
    logger.info(f"Get DataFrame Info tool result: {get_dataframe_info_tool_result}")

    calculate_max_tool_result = CalculateMax(dataframes_dict=dataframes_dict)._run(
        dataframe_key="202401_NFs_Cabecalho.csv", column="VALOR NOTA FISCAL"
    )
    logger.info(f"Calculate Max tool result: {calculate_max_tool_result}")

    calculate_mean_tool_result = CalculateMean(dataframes_dict=dataframes_dict)._run(
        dataframe_key="202401_NFs_Cabecalho.csv", column="VALOR NOTA FISCAL"
    )
    logger.info(f"Calculate Mean tool result: {calculate_max_tool_result}")

    logger.info("Pandas analysis tool successfully executed!")
