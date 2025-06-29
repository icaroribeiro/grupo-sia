import os

from crewai import LLM


class GeminiLLM:
    def create(self) -> LLM:
        return LLM(
            model="gemini/gemini-2.0-flash",
            temperature=0.2,
            api_key=os.environ["GEMINI_API_KEY"],
        )
