from langchain_openai import ChatOpenAI

from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.streamlit_app_error import StreamlitAppError


class LLM:
    def __init__(self, ai_settings: AISettings):
        self.__chat_model = self.__create_chat_model(ai_settings=ai_settings)

    @property
    def chat_model(self) -> ChatOpenAI:
        logger.info("Chat Model startup initiating...")
        if not self.__chat_model:
            message = f"Invalid LLM provider: {self.__provider}"
            logger.error(message)
            raise StreamlitAppError(message)
        message = "Chat Model startup complete."
        logger.info(message)
        return self.__chat_model

    @staticmethod
    def __create_chat_model(
        ai_settings: AISettings,
    ) -> ChatOpenAI:
        return ChatOpenAI(
            model=ai_settings.llm_model,
            temperature=ai_settings.llm_temperature,
            api_key=ai_settings.llm_api_key,
        )
