from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class UnzipFileAgent(BaseAgent):
    name: str = "unzip_file_agent"
    prompt: str = """
        ROLE:
        - You're an unzip file agent.
        GOAL:
        - Your sole purpose is to unzip files from ZIP archive.
        - DO NOT perform any other tasks.
    """
