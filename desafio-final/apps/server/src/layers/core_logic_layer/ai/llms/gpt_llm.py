import os

from crewai import LLM


class GptLLM:
    def create(self) -> LLM:
        return LLM(
            model="gpt-4.1-mini",
            temperature=0.1,
            api_key=os.environ["OPENAI_API_KEY"],
        )
