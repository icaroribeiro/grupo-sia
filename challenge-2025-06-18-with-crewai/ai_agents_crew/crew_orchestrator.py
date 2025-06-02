import asyncio
import traceback

from dotenv import load_dotenv
from ai_agents_crew.logger import logger
from ai_agents_crew.crews.message_response_crew import MessageResponseCrew

load_dotenv()


class CrewOrchestrator:
    async def run_orchestration(self, user_input_message: str) -> str:
        logger.info(f"Starting Message Response Crew for: {user_input_message}")
        inputs = {"user_message": user_input_message}
        message_response_crew = MessageResponseCrew().kickoff_crew()
        try:
            response = await message_response_crew.kickoff_async(inputs=inputs)
            logger.info("\nMessage Response Crew response: \n{response}\n")
            return response
        except Exception as err:
            logger.error(f"\nAn error occurred in Message Response Crew: {err}")
            traceback.print_exc()
            raise


if __name__ == "__main__":
    crew_orchestrator = CrewOrchestrator()
    user_input_message = "Hello, how are you today?"
    response = asyncio.run(
        crew_orchestrator.run_orchestration(user_input_message=user_input_message)
    )
    logger.info(f"Crew Orchestrator response: {response}")
