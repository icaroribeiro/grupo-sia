from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class UnzipFileAgent(BaseAgent):
    name: str = "unzip_file_agent"
    prompt: str = """
        ROLE:
        - You are an unzip file agent.
        
        GOAL:
        - Unzip a file based on the user's request.
    """
