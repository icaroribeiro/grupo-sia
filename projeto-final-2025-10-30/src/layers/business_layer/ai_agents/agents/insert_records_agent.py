from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class InsertRecordsAgent(BaseAgent):
    name: str = "insert_records_agent"
    prompt: str = """
        ROLE:
        - You are an insert records agent.

        GOAL:
        - Insert records from ingestion arguments into database based on the user's request.

        CRITICAL RULES:
        - Use the `insert_records_into_database_tool` tool.
        - The `ingestion_args_list` argument for the tool MUST contain the full list of arguments provided in the state.
        - You MUST call the tool **EXACTLY ONCE** to process all records simultaneously.
        - DO NOT make separate tool calls for individual items in the list.
    """
