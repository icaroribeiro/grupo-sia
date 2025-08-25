import pandas as pd
from pydantic import BaseModel


class DataFrameParams(BaseModel):
    name: str
    content: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True
