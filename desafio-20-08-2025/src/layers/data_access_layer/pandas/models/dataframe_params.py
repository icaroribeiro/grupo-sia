import pandas as pd
from pydantic import BaseModel


class DataFrameParams(BaseModel):
    name: str
    description: str
    content: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True
