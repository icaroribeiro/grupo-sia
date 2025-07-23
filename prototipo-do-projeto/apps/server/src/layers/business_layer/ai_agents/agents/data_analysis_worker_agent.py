from langchain_core.language_models import BaseChatModel

from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent
from langchain_core.tools import BaseTool
from langchain import hub


class DataAnalysisWorkerAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel, tools: list[BaseTool] = list()):
        prompt_template = hub.pull(
            owner_repo_commit="langchain-ai/sql-agent-system-prompt"
        )
        system_message = prompt_template.format(dialect="SQLite", top_k=5)
        super().__init__(
            name="data_analysis_worker_agent",
            llm=llm,
            tools=tools,
            prompt=system_message,
        )
