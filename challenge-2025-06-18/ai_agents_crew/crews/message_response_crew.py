from crewai import Crew, Process

from ai_agents_crew.agents.message_response_agent import MessageResponseAgent
from ai_agents_crew.llms.gemini_llm import GeminiLLM
from ai_agents_crew.tasks.message_response_task import MessageResponseTask


class MessageResponseCrew:
    def __init__(self):
        self.__llm = GeminiLLM().create_llm()

    def kickoff_crew(self) -> Crew:
        message_response_agent = MessageResponseAgent(llm=self.__llm).create_agent()

        message_response_task = MessageResponseTask().respond_message(
            agent=message_response_agent, user_message="{user_message}"
        )

        crew = Crew(
            agents=[message_response_agent],
            tasks=[message_response_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew
