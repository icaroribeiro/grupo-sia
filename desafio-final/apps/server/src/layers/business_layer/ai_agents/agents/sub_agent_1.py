from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field
from src.layers.business_layer.ai_agents.agents.base_agent import BaseAgent
from langchain_core.output_parsers import JsonOutputParser


class SubOutput(BaseModel):
    next: str = Field(description="The next node to route to")


class SubAgent_1(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(
            name="SubAgent_1",
            llm=llm,
            tools=[],
            prompt="""
                You are a sub agent responsible for routing tasks to a assistant agent.
                Current available assistants: [{assistant_names_str}].
                
                Analyze the user request and conversation history to determine 
                which assistant can handle it best.
                
                If the input messages indicate that the task is complete, or if 
                the state contains 'next': 'FINISH', return {finish_node}.
                
                Respond in the following JSON format:
                ```json
                {next_node}
                ```
                where <next_node> is the node to route to (e.g., {entry_node} 
                or {finish_node}).
            """,
        )

    def create_chain(
        self, assistant_names: list[str]
    ) -> Runnable[dict[str, list[BaseMessage]], dict[str, str]]:
        assistant_names_str = ", ".join(assistant_names)
        finish_node = '{{"next": "FINISH"}}'
        entry_node = (
            f'{{{{"next": "{assistant_names[0]}"}}}}'
            if assistant_names
            else '{{"next": "FINISH"}}'
        )
        next_node = '{{"next": "<next_node>"}}'
        options = str(["FINISH"] + assistant_names)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt.format(
                        assistant_names_str=assistant_names_str,
                        finish_node=finish_node,
                        entry_node=entry_node,
                        next_node=next_node,
                    ),
                ),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    """
                    Based on the conversation above, which subgraph should handle 
                    the request? Or should we FINISH? Select one of: {options}. 
                    
                    Respond with a JSON and nothing else: {{"next": "selected_option"}}
                    """,
                ),
            ]
        ).partial(
            assistant_names_str=", ".join(assistant_names_str),
            finish_node=finish_node,
            entry_node=entry_node,
            next_node=next_node,
            options=options,
        )

        # return (
        #     prompt
        #     | self.llm
        #     | RunnableLambda(lambda x: self.robust_json_parser(x, assistants))
        # )
        output_parser = JsonOutputParser(pydantic_object=SubOutput)
        return (prompt | self.llm | output_parser).with_config({"run_name": self.name})
