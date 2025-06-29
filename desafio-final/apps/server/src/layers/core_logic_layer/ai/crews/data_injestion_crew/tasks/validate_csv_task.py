from crewai import Agent, Task


class ValidateCSVTask:
    def create(self, csv_dir_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""
                Validate the CSV files at '{csv_dir_path}' against InvoiceDocument and InvoiceItemDocument schemas.
                If any error happens, abort the following tasks if any and just return an error message.
            """,
            expected_output=f"""
                A string indicating 'OK' if the CSV files at '{csv_dir_path}' were validated successfully, or an error message.
            """,
            async_execution=True,
            agent=agent,
        )
