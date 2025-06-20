import io
from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd
from crewai.tools import BaseTool

from ai_agents_crew.logger.logger import logger


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
        Get the head (first n rows) of a specified DataFrame.

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

        try:
            return f"Head of '{dataframe_key}':\n{dataframe.head(n).to_markdown(index=False)}"
        except Exception as err:
            return f"Error getting head from '{dataframe_key}': {err}"


class GetDataFrameInfoTool(BaseDataFrameTool):
    name: str = "Get DataFrame Info"
    description: str = """
        Get concise summary of a DataFrame, including data types and non-null values.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]

        try:
            buf = io.StringIO()
            dataframe.info(buf=buf)
            return f"Info for '{dataframe_key}':\n{buf.getvalue()}"
        except Exception as err:
            return f"Error getting info from '{dataframe_key}': {err}"


class FilterDataFrameTool(BaseDataFrameTool):
    name: str = "Filter DataFrame"
    description: str = """
        Filters a DataFrame based on a column and a specific value and returns the head (first n rows).

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            column (str): The DataFrame column name.
            value (str): The value to be filtered.
            n (int): The number of DataFrame rows to display.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, column: str, value: str, n: int = 10) -> str:
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
            return f"Filtered data from '{dataframe_key}':\n{filtered_dataframe.head(n).to_markdown(index=False)}"
        except Exception as err:
            return f"Error filtering data from '{dataframe_key}': {err}"


class MaxValueItemTool(BaseDataFrameTool):
    name: str = "Max Value Item"
    description: str = """
        Identifies the row with the highest value of a value column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            value_column (str): The column containing the values to compare.
            description_column (str): The column containing the item description.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(
        self, dataframe_key: str, value_column: str, description_column: str
    ) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if (
            value_column not in dataframe.columns
            or description_column not in dataframe.columns
        ):
            return f"Error: One or more specified columns not found in DataFrame '{dataframe_key}'."

        try:
            max_row = dataframe.loc[dataframe[value_column].idxmax()]
            return (
                f"Item with highest value:\n"
                f"Description: {max_row[description_column]}\n"
                f"Value: {max_row[value_column]:.2f}"
            )
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot identify the highest value."
        except Exception as err:
            return f"Error identifying the highest value for '{dataframe_key}': {err}"


class MinValueItemTool(BaseDataFrameTool):
    name: str = "Min Value Item"
    description: str = """
        Identifies the row with the lowest value of a value column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            value_column (str): The column containing the values to compare.
            description_column (str): The column containing the item description.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(
        self, dataframe_key: str, value_column: str, description_column: str
    ) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if (
            value_column not in dataframe.columns
            or description_column not in dataframe.columns
        ):
            return f"Error: One or more specified columns not found in DataFrame '{dataframe_key}'."

        try:
            min_row = dataframe.loc[dataframe[value_column].idxmin()]
            return (
                f"Item with lowest value:\n"
                f"Description: {min_row[description_column]}\n"
                f"Value: {min_row[value_column]:.2f}"
            )
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot identify the lowest value."
        except Exception as err:
            return f"Error identifying the lowest value for '{dataframe_key}': {err}"


class MeanColumnTool(BaseDataFrameTool):
    name: str = "Mean Column"
    description: str = """
        Calculates the mean of values of a value column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            value_column (str): The column to mean.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, value_column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if value_column not in dataframe.columns:
            return f"Error: Column '{value_column}' not found in DataFrame '{dataframe_key}'."

        try:
            mean_value = dataframe[value_column].mean()
            return f"Mean of '{value_column}' in '{dataframe_key}':\n{mean_value:.2f}"
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot calculate the mean value."
        except Exception as err:
            return f"Error calculating the mean value for '{dataframe_key}': {err}"


class SumColumnTool(BaseDataFrameTool):
    name: str = "Sum Column"
    description: str = """
        Calculates the sum of values of a value column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            value_column (str): The column to sum.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, value_column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if value_column not in dataframe.columns:
            return f"Error: Column '{value_column}' not found in DataFrame '{dataframe_key}'."

        try:
            total = dataframe[value_column].sum()
            return f"Total sum of '{value_column}' in '{dataframe_key}':\n{total:.2f}"
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot calculate the sum value."
        except Exception as err:
            return f"Error calculating the sum value for '{dataframe_key}': {err}"


class TopNBySumTool(BaseDataFrameTool):
    name: str = "Top N by Sum"
    description: str = """
        Finds the top n groups by sum of a value column, grouped by a specified column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            group_column (str): The column to group by.
            value_column (str): The column to sum.
            n (int): Number of top groups to return.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(
        self, dataframe_key: str, group_column: str, value_column: str, n: int = 5
    ) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if (
            group_column not in dataframe.columns
            or value_column not in dataframe.columns
        ):
            return f"Error: One or more specified columns not found in DataFrame '{dataframe_key}'."

        try:
            top_n = dataframe.groupby(group_column)[value_column].sum().nlargest(n)
            return f"Top {n} groups by sum of '{value_column}' in '{dataframe_key}':\n{top_n.to_markdown()}"
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot find top n groups by sum."
        except Exception as err:
            return f"Error finding top n group by sum for '{dataframe_key}': {err}"


class AverageByGroupTool(BaseDataFrameTool):
    name: str = "Average by Group"
    description: str = """
        Calculates the average of a value column, grouped by a specified column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            group_column (str): The column to group by.
            value_column (str): The column to average.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, group_column: str, value_column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if (
            group_column not in dataframe.columns
            or value_column not in dataframe.columns
        ):
            return f"Error: One or more specified columns not found in DataFrame '{dataframe_key}'."

        try:
            averages = dataframe.groupby(group_column)[value_column].mean()
            return f"Average by group of '{value_column}' in '{dataframe_key}':\n{averages.to_markdown()}"
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot calculate the average by group."
        except Exception as err:
            return (
                f"Error calculating the average by group for '{dataframe_key}': {err}"
            )


class CountByGroupTool(BaseDataFrameTool):
    name: str = "Count by Group"
    description: str = """
        Counts the number of rows per group in a specified column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            group_column (str): The column to group by.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, group_column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if group_column not in dataframe.columns:
            return f"Error: Column '{group_column}' not found in DataFrame '{dataframe_key}'."

        try:
            counts = dataframe[group_column].value_counts()
            return f"Counts by group in '{dataframe_key}':\n{counts.to_markdown()}"
        except Exception as err:
            return f"Error counting by group for '{dataframe_key}': {err}"


class SumByGroupTool(BaseDataFrameTool):
    name: str = "Sum by Group"
    description: str = """
        Calculates the sum of a value column, grouped by a specified column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            group_column (str): The column to group by.
            value_column (str): The column to sum.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, group_column: str, value_column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if (
            group_column not in dataframe.columns
            or value_column not in dataframe.columns
        ):
            return f"Error: One or more specified columns not found in DataFrame '{dataframe_key}'."

        try:
            sums = dataframe.groupby(group_column)[value_column].sum()
            return f"Sum by group:\n{sums.to_markdown()}"
        except TypeError:
            return f"Error: Column '{value_column}' in '{dataframe_key}' is not numeric. Cannot calculate the sum by group."
        except Exception as err:
            return f"Error calculating the sum by group for '{dataframe_key}': {err}"


class TopFrequentValuesTool(BaseDataFrameTool):
    name: str = "Top Frequent Values"
    description: str = """
        Identifies the most frequent values in a specified column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            column (str): The column to analyze.
            n (int): Number of top values to return.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, column: str, n: int = 5) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if column not in dataframe.columns:
            return f"Error: Column '{column}' not found in DataFrame '{dataframe_key}'."

        try:
            frequent = dataframe[column].value_counts().nlargest(n)
            return f"Top {n} frequent values:\n{frequent.to_markdown()}"
        except Exception as err:
            return f"Error identifying the top frequent values for '{dataframe_key}': {err}"


class DateRangeTool(BaseDataFrameTool):
    name: str = "Date Range"
    description: str = """
        Identifies the date range (earliest and latest) in a specified date column.

        Arguments:
            dataframe_key (str): The key to identify the DataFrame.
            date_column (str): The column containing dates.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(self, dataframe_key: str, date_column: str) -> str:
        if dataframe_key not in self.dataframes_dict:
            return f"Error: DataFrame '{dataframe_key}' not found."

        dataframe = self.dataframes_dict[dataframe_key]
        if date_column not in dataframe.columns:
            return f"Error: Column '{date_column}' not found in DataFrame '{dataframe_key}'."

        try:
            dataframe[date_column] = pd.to_datetime(dataframe[date_column])
            min_date = dataframe[date_column].min()
            max_date = dataframe[date_column].max()
            return f"Date range: {min_date} to {max_date}"
        except Exception as err:
            return f"Error identifying dates in '{dataframe_key}': {err}"


class JoinDataFramesTool(BaseDataFrameTool):
    name: str = "Join DataFrames"
    description: str = """
        Joins two DataFrames on specified columns and returns the head of the result.

        Arguments:
            left_dataframe_key (str): The key to identify the left DataFrame.
            right_dataframe_key (str): The key to identify the right DataFrame.
            left_column (str): The column in the left DataFrame to join on.
            right_column (str): The column in the right DataFrame to join on.
            join_type (str): The type of join (e.g., 'inner', 'left', 'right', 'outer').
            n (int): Number of rows to display from the joined DataFrame.
    """

    def __init__(self, dataframes_dict: Dict):
        super().__init__(dataframes_dict=dataframes_dict)

    def _run(
        self,
        left_dataframe_key: str,
        right_dataframe_key: str,
        left_column: str,
        right_column: str,
        join_type: str = "inner",
        n: int = 5,
    ) -> str:
        if (
            left_dataframe_key not in self.dataframes_dict
            or right_dataframe_key not in self.dataframes_dict
        ):
            return f"Error: One or both DataFrames ('{left_dataframe_key}', '{right_dataframe_key}') not found."

        left_dataframe = self.dataframes_dict[left_dataframe_key]
        right_dataframe = self.dataframes_dict[right_dataframe_key]
        if (
            left_column not in left_dataframe.columns
            or right_column not in right_dataframe.columns
        ):
            return "Error: One or more join columns not found in DataFrames."

        try:
            joined_dataframe = pd.merge(
                left_df,
                right_df,
                how=join_type,
                left_on=left_column,
                right_on=right_column,
            )
            if joined_dataframe.empty:
                return f"No matching rows found after joining '{left_dataframe_key}' and '{right_dataframe_key}'."
            return f"Joined data:\n{joined_dataframe.head(n).to_markdown(index=False)}"
        except Exception as err:
            return f"Error joining '{left_dataframe_key}' and '{right_dataframe_key}': {err}"


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

    # calculate_max_tool_result = CalculateMax(dataframes_dict=dataframes_dict)._run(
    #     dataframe_key="202401_NFs_Cabecalho.csv", column="VALOR NOTA FISCAL"
    # )
    # logger.info(f"Calculate Max tool result: {calculate_max_tool_result}")

    # calculate_mean_tool_result = CalculateMean(dataframes_dict=dataframes_dict)._run(
    #     dataframe_key="202401_NFs_Cabecalho.csv", column="VALOR NOTA FISCAL"
    # )
    # logger.info(f"Calculate Mean tool result: {calculate_max_tool_result}")

    logger.info("Pandas analysis tool successfully executed!")
