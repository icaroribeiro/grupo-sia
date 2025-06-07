from crewai import LLM
from dotenv import load_dotenv

from ai_agents_crew.llms.chatgpt_llm import ChatGPTLLM
from ai_agents_crew.llms.gemini_llm import GeminiLLM
from ai_agents_crew.logger.logger import logger
from ai_agents_crew.settings.settings import get_settings

load_dotenv()


def get_llm() -> LLM:
    if not get_settings().OPENAI_API_KEY:
        logger.warning("""
            OPENAI_API_KEY not found. 
            You must set up an API key in your .env file or environment variables.
        """)
    else:
        return ChatGPTLLM().create()

    if not get_settings().GEMINI_API_KEY:
        logger.warning("""
            GEMINI_API_KEY not found. 
            You must set up an API key in your .env file or environment variables.
        """)
    else:
        return GeminiLLM().create()

    raise Exception("No API Key found")


llm = get_llm()
