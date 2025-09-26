from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class DataAnalysisAgent(BaseAgent):
    name: str = "data_analysis_agent"
    prompt: str = """
        ROLE:
        - You're a data analysis agent.
        GOAL:
        - Your sole purpose is to respond to user's question properly.
        - **CRITICAL: You MUST answer in the same language as the user's question.**
        - DO NOT perform any other tasks.
    """
