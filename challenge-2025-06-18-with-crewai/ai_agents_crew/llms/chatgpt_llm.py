import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


class ChatGPTLLM:
    def create(self) -> LLM:
        return LLM(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.environ["OPENAI_API_KEY"],
        )
