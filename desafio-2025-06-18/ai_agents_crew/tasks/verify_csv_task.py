from crewai import Agent, Task


class VerifyCSVTask:
    def create(self, csv_file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""
                Confirm the readability of the following CSV file '{csv_file_path}'.
                If any error happens, abort the following tasks if any and just return an error message.
            """,
            expected_output=f"""
                A string indicating 'OK' if '{csv_file_path}' was read successfully, or an error message.
            """,
            agent=agent,
        )
