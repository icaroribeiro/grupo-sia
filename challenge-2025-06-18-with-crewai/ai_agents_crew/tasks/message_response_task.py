from crewai import Task, Agent


class MessageResponseTask:
    def respond_message(self, agent: Agent, user_message: str) -> Task:
        return Task(
            description=(
                "Analyze the following user message: '{user_message}' "
                "and generate a polite, informative, and helpful response. "
                "Keep your response concise and directly answer the user's query."
            ),
            expected_output="""
                A helpful and engaging response to the user's message
            """,
            agent=agent,
        )
