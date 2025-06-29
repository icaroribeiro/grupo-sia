from crewai import Agent, Task


class UnzipFileTask:
    def create(self, zip_path: str, csv_dir_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""
                Unzip the CSV file from the provided ZIP file '{zip_path}' to the '{csv_dir_path}' directory.
                If any error happens, abort the following tasks if any and just return an error message.
            """,
            expected_output=f"""
                A string indicating 'OK' if the ZIP file '{zip_path}' was unzipped successfully, or an error message.
            """,
            async_execution=True,
            agent=agent,
        )
