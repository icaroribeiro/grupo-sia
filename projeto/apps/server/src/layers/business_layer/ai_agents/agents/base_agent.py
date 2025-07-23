from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


class BaseAgent:
    def __init__(
        self,
        name: str,
        llm: BaseChatModel,
        tools: list[BaseTool],
        prompt: str,
    ):
        self.name: str = name
        self.llm: BaseChatModel = llm
        self.tools: list[BaseTool] = tools
        self.prompt: str = prompt
