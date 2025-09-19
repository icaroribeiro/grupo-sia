from crewai import LLM
from dotenv import load_dotenv

from ai_agents_crew.llms.gemini_llm import GeminiLLM
from ai_agents_crew.llms.openai_llm import OpenAILLM
from ai_agents_crew.logger.logger import logger
from ai_agents_crew.settings.settings import get_settings

load_dotenv()


def get_llm() -> LLM:
    if get_settings().LLM.lower() not in ["gpt", "gemini"]:
        logger.error("""
            LLM not found. 
            You must set up a LLM in your .env file or environment variables.
        """)
        raise Exception("LLM not found!")

    if get_settings().LLM.lower() == "gpt":
        if not get_settings().OPENAI_API_KEY:
            logger.error("""
                OPENAI_API_KEY not found. 
                You must set up an API key in your .env file or environment variables.
            """)
            raise Exception("API key not found!")
        else:
            return OpenAILLM().create()

    if get_settings().LLM.lower() == "gemini":
        if not get_settings().GEMINI_API_KEY:
            logger.error("""
                GEMINI_API_KEY not found. 
                You must set up an API key in your .env file or environment variables.
            """)
            raise Exception("API key not found!")
        else:
            return GeminiLLM().create()
