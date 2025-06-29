from src.layers.core_logic_layer.ai.llms.gemini_llm import GeminiLLM
from src.layers.core_logic_layer.ai.llms.gpt_llm import GptLLM
from crewai import LLM
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.settings import get_settings


def setup_llm() -> LLM:
    if get_settings().llm.lower() not in ["gpt", "gemini"]:
        logger.error("""
            LLM not found. 
            You must set up a LLM in your .env file or environment variables.
        """)
        raise Exception("LLM not found!")

    if get_settings().LLM.lower() == "gpt":
        if not get_settings().openai_api_key:
            logger.error("""
                OPENAI_API_KEY not found. 
                You must set up an API key in your .env file or environment variables.
            """)
            raise Exception("API key not found!")
        else:
            return GptLLM().create()

    if get_settings().llm.lower() == "gemini":
        if not get_settings().gemini_api_key:
            logger.error("""
                GEMINI_API_KEY not found. 
                You must set up an API key in your .env file or environment variables.
            """)
            raise Exception("API key not found!")
        else:
            return GeminiLLM().create()
