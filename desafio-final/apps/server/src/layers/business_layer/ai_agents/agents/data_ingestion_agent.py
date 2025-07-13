# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI

# from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent
# from src.layers.business_layer.ai_agents.tools.test_tools import GetIcarosAgeTool


# class DataIngestionAgent(BaseAgent):
#     def __init__(
#         self,
#         llm: ChatGoogleGenerativeAI | ChatOpenAI,
#     ):
#         super().__init__(llm=llm, tools=[GetIcarosAgeTool()])

#         # system_prompt = """
#         # You are an AI agent. Just respond to queries.
#         # """

#         # super().__init__(llm=llm, tools=tools, system_prompt=system_prompt)
