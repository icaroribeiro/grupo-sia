from langgraph.graph import StateGraph
from pydantic import BaseModel, ConfigDict


class BaseStateGraphModel(BaseModel):
    name: str
    graph: StateGraph

    model_config = ConfigDict(arbitrary_types_allowed=True)
