from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda

from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class SupervisorAgent_1(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(
            name="SupervisorAgent_1",
            llm=llm,
            tools=[],
            prompt="""
                You are a supervisor tasked with managing a conversation between the following assistants: {assistants}. 
                Given the user request and conversation history, respond with a JSON object containing a single key 'next'
                whose value is either one of the assistants or 'FINISH'. 
                Choose the worker who should act next based on the context, or 'FINISH' if the task is complete. 
                Return valid JSON fenced by a markdown code block, e.g., {first_example} or {second_example}.
                Do not return any additional text.
            """,
        )

    def create_chain(
        self, assistants: list[str]
    ) -> Runnable[dict[str, list[BaseMessage]], dict[str, str]]:
        first_example = '{{"next": "Assistant_2"}}'
        second_example = '{{"next": "FINISH"}}'
        options = str(["FINISH"] + assistants)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt.format(
                        assistants=assistants,
                        first_example=first_example,
                        second_example=second_example,
                    ),
                ),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    """
                    Given the conversation above, including any ToolMessage outputs, who should act next? Or should we FINISH? "
                    Select one of: {options}. Respond with a JSON and nothing else: {{"next": "selected_option"}}
                    """,
                ),
            ]
        ).partial(
            assistants=", ".join(assistants),
            first_example=first_example,
            second_exampe=second_example,
            options=options,
        )

        return (
            prompt
            | self.llm
            | RunnableLambda(lambda x: self.robust_json_parser(x, assistants))
        )
