from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda

from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent


class ManagerAgent_1(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(
            name="ManagerAgent_1",
            llm=llm,
            tools=[],
            prompt="""
                You are a manager tasked with routing user requests to one of the following subgraphs: {subgraphs}.
                Analyze the user request and conversation history to determine which subgraph can handle it best, or choose 'FINISH' if the task is complete.
                - Subgraph_2 handles multi-agent tasks with a supervisor, such as complex workflows involving multiple assistants.
                Respond with a JSON object containing a single key 'next' whose value is either a subgraph name or 'FINISH'.
                Return valid JSON fenced by a markdown code block, e.g., {first_example} or {second_example}.
                Do not return any additional text.
            """,
        )

    def create_chain(
        self, subgraphs: list[str]
    ) -> Runnable[dict[str, list[BaseMessage]], dict[str, str]]:
        first_example = (
            f'{{{{"next": "{subgraphs[0]}"}}}}' if subgraphs else '{{"next": "FINISH"}}'
        )
        second_example = '{{"next": "FINISH"}}'
        print(f"\n\nfirst: {first_example}")
        print(f"\n\nsecond: {second_example}")
        # first_example = '{{"next": "Subgraph_2"}}'
        # second_example = '{{"next": "FINISH"}}'
        options = str(["FINISH"] + subgraphs)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt.format(
                        subgraphs=subgraphs,
                        first_example=first_example,
                        second_example=second_example,
                    ),
                ),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    """
                    Based on the conversation above, which subgraph should handle the request? Or should we FINISH?
                    Select one of: {options}. Respond with a JSON and nothing else: {{"next": "selected_option"}}
                    """,
                ),
            ]
        ).partial(
            subgraphs=", ".join(subgraphs),
            first_example=first_example,
            second_example=second_example,
            options=options,
        )

        return (
            prompt
            | self.llm
            | RunnableLambda(lambda x: self.robust_json_parser(x, subgraphs))
        )
