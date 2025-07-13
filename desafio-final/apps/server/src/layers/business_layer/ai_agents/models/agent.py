from openai import BaseModel
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import Field


class Agent(BaseModel):
    name: str
    prompt: str
    llm: ChatGoogleGenerativeAI | ChatOpenAI
    tools: list[BaseTool] = Field(default=list())
