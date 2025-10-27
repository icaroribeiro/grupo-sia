from src.streamlit_app_layers.ai_layer.agents.base_agent import BaseAgent


class UnzipFileAgent(BaseAgent):
    name: str = "unzip_file_agent"
    prompt: str = """
        ROLE:
        - You are an unzip file agent.
        
        OBJECTIVE:
        - You are responsible for unzipping a ZIP file based on the user's request.
        
        INSTRUCTIONS: 
        - If the assigned task involves unzipping a ZIP file, use the `unzip_zip_file_tool` to unzip the ZIP file.
        
        CRITICAL RULES:
        - **NEVER** return a conversational response, a summary, or route back to the supervisor without executing the task assigned.
    """
