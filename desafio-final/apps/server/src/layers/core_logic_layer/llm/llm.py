from typing import Union
from langchain_google_genai import GoogleGenerativeAI
from langchain_openai import ChatOpenAI


class LLM:
    def __init__(self, llm_params: dict[str, Union[str, float]]):
        self.__llm_params = llm_params

    @property
    def custom_llm(self) -> ChatOpenAI | GoogleGenerativeAI:
        match self.__llm_params["provider"]:
            case "openai":
                return ChatOpenAI(
                    model=self.__llm_params["model"],
                    temperature=self.__llm_params["temperature"],
                    api_key=self.__llm_params["api_key"],
                )
            case "google_genai":
                return GoogleGenerativeAI(
                    model=self.__llm_params["model"],
                    temperature=self.__llm_params["temperature"],
                    api_key=self.__llm_params["api_key"],
                )
            case _:
                raise Exception("Erro")
