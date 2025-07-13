from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from typing import List


class WorkflowSupervisor:
    def __init__(self, members: List[str]):
        pass
        # self.members = members
        # self.options = ["FINISH"] + members
        # self.logger.info(
        #     f"Initializing SupervisorWorkflow with members: {', '.join(members)}"
        # )
        # # Initialize LLM
        # self.llm = ChatGoogleGenerativeAI(
        #     model="gemini-1.5-pro",
        #     google_api_key=os.getenv("GOOGLE_API_KEY"),
        #     temperature=0,
        # )
        # # Define supervisor chain
        # self.supervisor_chain = self._build_supervisor_chain()
        # self.graph = self._build_graph()

    @property
    def supervisor_chain(self):
        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the following workers: {members}. "
            "Given the user request and conversation history, respond with a JSON object containing a single key 'next' "
            "whose value is either one of the workers or 'FINISH'. "
            "Choose the worker who should act next based on the context, or 'FINISH' if the task is complete. "
            "Return only the JSON object, e.g., {{'next': 'worker1'}} or {{'next': 'FINISH'}}."
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    "Given the conversation above, who should act next? Or should we FINISH? "
                    "Select one of: {options}. Respond with a JSON object: {{'next': 'selected_option'}}",
                ),
            ]
        ).partial(options=str(self.options), members=", ".join(self.members))

        return prompt | self.llm | JsonOutputParser()
