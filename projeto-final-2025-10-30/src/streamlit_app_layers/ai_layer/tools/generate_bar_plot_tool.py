import json
from typing import Type, Tuple, Dict, Any

import altair as alt
import pandas as pd
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field

from src.streamlit_app_layers.core_layer.logging import logger
from src.streamlit_app_layers.data_access_layer.db.postgresql import PostgreSQL


class GenerateBarPlotToolInput(BaseModel):
    sql_query: str = Field(
        default=...,
        description="The SQL query to execute against the database. Must be a SELECT query.",
    )
    column_name: str = Field(
        default=...,
        description="The name of the categorical column to calculate and plot the frequency counts for.",
    )


class GenerateBarPlotTool(BaseTool):
    name: str = "generate_bar_plot_tool"
    description: str = (
        "Generates a bar chart visualizing the frequency count for up to 20 unique "
        "categories in a specified column. Use this tool for **categorical** or **ordinal** data only."
    )
    postgresql: PostgreSQL
    args_schema: Type[BaseModel] = GenerateBarPlotToolInput
    response_format: str = "content_and_artifact"

    def __init__(self, postgresql: PostgreSQL):
        super().__init__(postgresql=postgresql)
        self.postgresql = postgresql

    def _run(self, sql_query: str, column_name: str) -> Tuple[str, Dict[str, Any]]:
        logger.info(
            f"Calling {self.name} with sql_query={sql_query}, column_name={column_name}..."
        )
        try:
            if not sql_query or not sql_query.lower().startswith("select"):
                raise ValueError("Query must start with 'SELECT' and cannot be empty.")

            df = pd.read_sql(sql_query, self.postgresql.sync_engine)

            if df is None or df.empty:
                raise ValueError("DataFrame is None or empty. Query returned no data.")

            if column_name not in df.columns:
                raise ValueError(f"Column '{column_name}' not found in DataFrame.")

            col_data = df[column_name].dropna()

            if pd.api.types.is_numeric_dtype(col_data):
                raise ValueError(
                    f"Column '{column_name}' is numeric. Use 'generate_distribution_plot_tool' "
                    "for its distribution instead of a bar chart."
                )

            counts_df = col_data.value_counts().reset_index().head(20)
            counts_df.columns = [column_name, "count"]

            altair_type = "N"

            chart = (
                alt.Chart(counts_df)
                .mark_bar(opacity=0.8, color="#4682b4")
                .encode(
                    x=alt.X(
                        f"{column_name}:{altair_type}", title=column_name, sort="-y"
                    ),
                    y=alt.Y("count:Q", title="Frequência (Contagem)"),
                    tooltip=[
                        alt.Tooltip(f"{column_name}:{altair_type}", title=column_name),
                        alt.Tooltip("count:Q", title="Contagem"),
                    ],
                )
                .properties(
                    title=f"Frequência das Principais Categorias em {column_name}",
                    width=400,
                    height=300,
                )
            )

            total_records = len(df)
            top_categories_count = len(counts_df)

            content = (
                f"Gráfico de barras gerado. Exibindo a frequência das top {top_categories_count} categorias "
                f"para a coluna '{column_name}' (de um total de {total_records} registros)."
            )

            artifact = json.loads(chart.to_json())

            logger.info(f"Bar plot generated for {column_name}")
            return content, artifact

        except Exception as error:
            message = f"Bar plot not generated: {type(error).__name__} - {str(error)}"
            logger.error(message)
            raise ToolException(message)

    async def _arun(
        self, sql_query: str, column_name: str
    ) -> Tuple[str, Dict[str, Any]]:
        return self._run(sql_query=sql_query, column_name=column_name)
