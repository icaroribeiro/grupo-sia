from pydantic import BaseModel, ConfigDict
from langgraph.graph import StateGraph


class StateGraphModel(BaseModel):
    name: str
    graph: StateGraph

    model_config = ConfigDict(arbitrary_types_allowed=True)
