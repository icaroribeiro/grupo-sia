from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.server_error import ServerError


class LLM:
    def __init__(self, ai_settings: AISettings):
        self.__llm = self.__create_llm(ai_settings=ai_settings)

    @property
    def llm(self) -> ChatOpenAI | ChatGoogleGenerativeAI:
        logger.info("LLM startup initiating...")
        if self.__llm:
            message = "Success: LLM startup complete."
            logger.info(message)
            return self.__llm
        message = f"Error: Invalid LLM provider: {self.__provider}"
        logger.error(message)
        raise ServerError(message)

    @staticmethod
    def __create_llm(
        ai_settings: AISettings,
    ) -> ChatOpenAI | ChatGoogleGenerativeAI | None:
        match ai_settings.llm_provider:
            case "openai":
                return ChatOpenAI(
                    model=ai_settings.llm_model,
                    temperature=ai_settings.llm_temperature,
                    api_key=ai_settings.llm_api_key,
                )
            case "google_genai":
                return ChatGoogleGenerativeAI(
                    model=ai_settings.llm_model,
                    temperature=ai_settings.llm_temperature,
                    api_key=ai_settings.llm_api_key,
                )
            case _:
                return None
