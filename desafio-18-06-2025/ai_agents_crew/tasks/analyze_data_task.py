from crewai import Agent, Task


class AnalyzeDataTask:
    def create(self, user_query: str, available_dfs_str: str, agent: Agent) -> Task:
        return Task(
            description=f"""
                Analyze the available dataframes ({available_dfs_str}) to answer the following user's query: '{user_query}'.
                Use the provided pandas tools to extract relevant information. 
                Summarize your findings clearly and concisely, highlighting key observations and any relevant statistics.
                Explicitly mention which dataframe(s) you are referring to for each finding.
            """,
            expected_output="""
                A concise summary of the data analysis findings, addressing the user's query.
            """,
            agent=agent,
        )
