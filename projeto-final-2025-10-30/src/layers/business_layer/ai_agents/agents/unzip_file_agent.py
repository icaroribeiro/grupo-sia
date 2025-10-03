from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class UnzipFileAgent(BaseAgent):
    name: str = "unzip_file_agent"
    prompt: str = """
        ROLE:
        - You are an unzip file agent.        
        GOAL:
        - Unzip a ZIP file based on the user's request.
        CRITICAL RULES:
        - Use the `unzip_zip_file_tool` tool for unzip a ZIP file.
    """
