import os
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


class GeminiLLM:
    def create_llm(self):
        return LLM(
            model="gemini/gemini-2.0-flash",
            temperature=0.1,
            api_key=os.environ["GEMINI_API_KEY"],
        )
