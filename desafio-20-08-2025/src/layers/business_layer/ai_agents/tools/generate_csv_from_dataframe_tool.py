import os
import pandas as pd
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.business_layer.ai_agents.models.tool_output import Status, ToolOutput
from src.layers.core_logic_layer.logging import logger


class GenerateCsvFromDataFrameInput(BaseModel):
    df: Type[pd.DataFrame] = Field(
        ..., description="The pandas DataFrame to save to a CSV file."
    )
    output_path: str = Field(..., description="The full path to the output CSV file.")


class GenerateCsvFromDataFrameTool(BaseTool):
    name: str = "generate_csv_from_dataframe_tool"
    description: str = (
        "Generates a CSV file from a pandas DataFrame and saves it to a specified path."
    )
    args_schema: Type[BaseModel] = GenerateCsvFromDataFrameInput

    def _run(self, df: pd.DataFrame, output_path: str) -> ToolOutput:
        logger.info(f"Calling {self.name}...")
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Use pandas.DataFrame.to_csv() to generate the CSV file
            df.to_csv(output_path, index=False)

            return ToolOutput(
                status=Status.SUCCEED,
                result=f"Successfully generated CSV file at: {output_path}",
            )
        except Exception as error:
            message = f"Error generating CSV: {str(error)}"
            logger.error(message)
            return ToolOutput(status=Status.FAILED, result=None)

    async def _arun(self, df: pd.DataFrame, output_path: str) -> ToolOutput:
        return self._run(df=df, output_path=output_path)
