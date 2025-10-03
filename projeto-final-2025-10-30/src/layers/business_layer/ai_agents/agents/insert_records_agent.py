from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class InsertRecordsAgent(BaseAgent):
    name: str = "insert_records_agent"
    prompt: str = """
        ROLE:
        - You are an insert records agent.
        GOAL:
        - Insert records from ingestion arguments into database based on the user's request.
        CRITICAL RULES:
        - Use the `insert_records_into_database_tool` tool for insert records from ingestion arguments into database.
    """
