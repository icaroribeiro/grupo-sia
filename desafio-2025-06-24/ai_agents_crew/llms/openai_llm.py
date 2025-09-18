import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


class OpenAILLM:
    def create(self) -> LLM:
        return LLM(
            model="gpt-4.1-mini",
            temperature=0.1,
            api_key=os.environ["OPENAI_API_KEY"],
        )
