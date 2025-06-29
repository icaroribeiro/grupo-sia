from crewai import Agent, Task


class InsertMongoTask:
    def create(self, csv_dir_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""
                Insert data from validated CSV files at '{csv_dir_path}' into MongoDB for InvoiceDocument and InvoiceItemDocument.
                If any error happens, abort the following tasks if any and just return an error message.
            """,
            expected_output=f"""
                A string indicating 'OK' if the validated CSV files at '{csv_dir_path}' were inserted into MongoDB successfully, or an error message.
            """,
            async_execution=True,
            agent=agent,
        )
