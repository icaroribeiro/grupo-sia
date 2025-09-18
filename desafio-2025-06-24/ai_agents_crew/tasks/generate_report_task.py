from crewai import Agent, Task


class GenerateReportTask:
    def create(self, user_query: str, analysis_summary: str, agent: Agent) -> Task:
        return Task(
            description=f"""
                Based on the analysis summary: '{analysis_summary}', create an objective response
                acknowledging the original user's query: '{user_query}'.
            """,
            expected_output="""
                A straightforward response summarizing the analysis findings for the user.
                The response must always be written in the same language as the user's query.
            """,
            agent=agent,
        )
