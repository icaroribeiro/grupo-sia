import json
from typing import Annotated, Type, Tuple, Dict, Any

import altair as alt
import numpy as np
import pandas as pd
from langchain_core.tools import BaseTool, InjectedToolCallId, ToolException
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class GenerateDistributionToolInput(BaseModel):
    column_name: str = Field(default=..., description="The name of the column to plot")
    split_by: str | None = Field(
        default=None, description="Optional column to split the distribution by"
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(default=...)


class GenerateDistributionTool(BaseTool):
    name: str = "generate_distribution_tool"
    description: str = "Generates a distribution plot (histogram) for a specified column in the injected DataFrame 'df'. Can split the distribution by another column. This tool is optimized for large datasets."
    args_schema: Type[BaseModel] = GenerateDistributionToolInput
    response_format: str = "content_and_artifact"
    dataframe: pd.DataFrame

    def __init__(self, dataframe: pd.DataFrame):
        super().__init__(dataframe=dataframe)
        self.dataframe = dataframe

    def _run(
        self, column_name: str, tool_call_id: str, split_by: str | None = None
    ) -> Tuple[str, Dict[str, Any]]:
        logger.info(
            f"Calling {self.name} with column_name={column_name}, split_by={split_by}..."
        )
        try:
            if self.dataframe is None or self.dataframe.empty:
                raise ValueError("DataFrame is None or empty")
            if column_name not in self.dataframe.columns:
                raise ValueError(f"Column '{column_name}' not found in DataFrame")
            if split_by and split_by not in self.dataframe.columns:
                raise ValueError(f"Split column '{split_by}' not found in DataFrame")

            num_bins = 20
            col_data = self.dataframe[column_name].dropna()
            min_val, max_val = col_data.min(), col_data.max()
            bin_edges = np.linspace(min_val, max_val, num_bins + 1)

            hist_df = None
            if split_by:
                agg_data = []
                for group_name, group_df in self.dataframe.groupby(split_by):
                    counts, _ = np.histogram(
                        group_df[column_name].dropna(), bins=bin_edges
                    )
                    group_hist = pd.DataFrame(
                        {
                            "bin_start": bin_edges[:-1],
                            "bin_end": bin_edges[1:],
                            "count": counts,
                            split_by: group_name,
                        }
                    )
                    agg_data.append(group_hist)
                hist_df = pd.concat(agg_data, ignore_index=True)
            else:
                counts, _ = np.histogram(col_data, bins=bin_edges)
                hist_df = pd.DataFrame(
                    {
                        "bin_start": bin_edges[:-1],
                        "bin_end": bin_edges[1:],
                        "count": counts,
                    }
                )

            chart = (
                alt.Chart(hist_df)
                .mark_bar(opacity=0.7)
                .encode(
                    x=alt.X(
                        "bin_start:Q",
                        title=f"{column_name}",
                        axis=alt.Axis(format="~s"),
                    ),
                    x2=alt.X2("bin_end:Q"),
                    y=alt.Y("count:Q", title="Contador de Registros"),
                    color=(
                        alt.Color(f"{split_by}:N", title=split_by)
                        if split_by
                        else alt.value("#4682b4")
                    ),
                    tooltip=(
                        [
                            alt.Tooltip(
                                "bin_start:Q", title=f"Start of {column_name} bin"
                            ),
                            alt.Tooltip("bin_end:Q", title=f"End of {column_name} bin"),
                            alt.Tooltip("count:Q", title="Count of Records"),
                            alt.Tooltip(f"{split_by}:N", title=split_by),
                        ]
                        if split_by
                        else [
                            alt.Tooltip(
                                "bin_start:Q", title=f"Start of {column_name} bin"
                            ),
                            alt.Tooltip("bin_end:Q", title=f"End of {column_name} bin"),
                            alt.Tooltip("count:Q", title="Count of Records"),
                        ]
                    ),
                )
                .properties(
                    title=f"Distribuição de {column_name}{' pela ' + split_by if split_by else ''}",
                    width=400,
                    height=300,
                )
            )

            skewness = self.dataframe[column_name].skew()
            content = f"Distribuiçao de {column_name}{' separado por ' + split_by if split_by else ''}. Assimetria: {skewness:.2f}"

            artifact = json.loads(chart.to_json())

            logger.info(f"Chart generated for {column_name}")
            return content, artifact

        except Exception as error:
            message = (
                f"Distribution not generated: {type(error).__name__} - {str(error)}"
            )
            logger.error(message)
            raise ToolException(message)

    async def _arun(
        self, column_name: str, tool_call_id: str, split_by: str | None = None
    ) -> Tuple[str, Dict[str, Any]]:
        return self._run(
            column_name=column_name, tool_call_id=tool_call_id, split_by=split_by
        )
