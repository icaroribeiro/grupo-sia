from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class CSVMappingAgent(BaseAgent):
    name: str = "csv_mapping_agent"
    prompt: str = """
        ROLE:
        - You are a csv mapping agent.        
        GOAL:
        - Map extracted csv files into ingestion arguments based on the user's request.
        CRITICAL RULES:
        - Use the `map_csvs_to_ingestion_args_tool` tool for map extracted csv files into ingestion arguments.
    """
