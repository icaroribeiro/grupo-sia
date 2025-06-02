from typing import Any
from crewai import Agent, BaseLLM
from pydantic import InstanceOf


class MessageResponseAgent:
    def __init__(self, llm: str | InstanceOf[BaseLLM] | Any = None):
        self.__llm = llm

    def create_agent(self):
        return Agent(
            role="Message Responder",
            goal="""
                Respond to the user messages in a helpful and engaging way.
            """,
            backstory="""
                You are a friendly and intelligent AI assistant ready to chat.
            """,
            llm=self.__llm,
            verbose=True,
            allow_delegation=False,
        )
