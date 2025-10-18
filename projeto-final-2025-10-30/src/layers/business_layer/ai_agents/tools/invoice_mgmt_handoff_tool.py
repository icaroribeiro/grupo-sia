from typing import Annotated, Type, Tuple

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class InvoiceMgmtHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next agent should do, including all of the relevant context."
        ),
    ]


class InvoiceMgmtHandoffTool(BaseTool):
    name: str = "data_analysis_handoff_tool"
    description: str | None = (
        "Hands off a task to another agent with a description and relevant context."
    )
    agent_name: str
    args_schema: Type[BaseModel] = InvoiceMgmtHandoffToolInput
    response_format: str = "content_and_artifact"

    def __init__(self, agent_name: str):
        super().__init__(agent_name=agent_name)
        self.name = f"delegate_to_{agent_name}_tool"
        self.agent_name = agent_name

    async def _arun(
        self,
        task_description: str,
    ) -> Tuple[str, Tuple[str, str]]:
        logger.info(f"Executing handoff to {self.agent_name}...")
        logger.info(f"Task description for next agent: {task_description}")

        content = f"Task successfully delegated to {self.agent_name} with the task: '{task_description[:50]}...'"

        artifact = (self.agent_name, task_description)

        return content, artifact

    def _run(
        self,
        task_description: Annotated[
            str,
            Field(
                description="Description of what the next agent should do, including all of the relevant context."
            ),
        ],
    ) -> Tuple[str, Tuple[str, str]]:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
