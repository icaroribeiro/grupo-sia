import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


class GeminiLLM:
    def create(self) -> LLM:
        return LLM(
            model="gemini-2.0-flash",
            temperature=0.2,
            api_key=os.environ["GEMINI_API_KEY"],
        )
