from crewai import Agent, Task


class UnzipFileTask:
    def create(
        self, zip_file_to_process: str, extracted_dir: str, agent: Agent
    ) -> Task:
        return Task(
            description=f"""
                Unzip the following file '{zip_file_to_process}' to the '{extracted_dir}' directory.
                If any error happens, abort the following tasks if any and just return an error message.
            """,
            expected_output=f"""
                A string indicating 'OK' if '{zip_file_to_process}' was unzipped successfully, or an error message.
            """,
            agent=agent,
        )
