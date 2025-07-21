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
                You are a sub agent responsible for routing tasks to a worker agent.
                Current available workers: [{worker_names_str}].
                
                Analyze the user request and conversation history to determine 
                which worker can handle it best.
                
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

    def create_llm_chain(
        self, worker_names: list[str]
    ) -> Runnable[dict[str, list[BaseMessage]], dict[str, str]]:
        worker_names_str = ", ".join(worker_names)
        finish_node = '{{"next": "FINISH"}}'
        entry_node = (
            f'{{{{"next": "{worker_names[0]}"}}}}'
            if worker_names
            else '{{"next": "FINISH"}}'
        )
        next_node = '{{"next": "<next_node>"}}'
        options = str(["FINISH"] + worker_names)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt.format(
                        worker_names_str=worker_names_str,
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
            worker_names_str=", ".join(worker_names_str),
            finish_node=finish_node,
            entry_node=entry_node,
            next_node=next_node,
            options=options,
        )

        # return (
        #     prompt
        #     | self.llm
        #     | RunnableLambda(lambda x: self.robust_json_parser(x, workers))
        # )
        chain = prompt | self.llm | JsonOutputParser(pydantic_object=SubOutput)
        return chain.with_config(config={"run_name": self.name})
