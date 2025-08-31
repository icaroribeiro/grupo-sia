from typing import Annotated, Type

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class DataReportingHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next agent should do, including all of the relevant context."
        ),
    ]
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class DataReportingHandoffTool(BaseTool):
    name: str = "handoff_tool"
    description: str | None = (
        "Hands off a task to another agent with a description and relevant context."
    )
    agent_name: str
    args_schema: Type[BaseModel] = DataReportingHandoffToolInput

    def __init__(
        self,
        agent_name: str,
        description: str | None = None,
    ):
        super().__init__(agent_name=agent_name)
        self.name = f"transfer_to_{agent_name}"
        self.agent_name = agent_name
        self.description = description or f"Ask {agent_name} for help."

    async def _arun(
        self,
        task_description: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        logger.info(f"Executing handoff to {self.agent_name}...")
        logger.info(f"Task description for next agent: {task_description}")
        return ToolMessage(
            content=f"transfer_to_agent:{self.agent_name}::task:{task_description}",
            name=self.name,
            tool_call_id=tool_call_id,
        )

    def _run(
        self,
        task_description: Annotated[
            str,
            Field(
                description="Description of what the next agent should do, including all of the relevant context."
            ),
        ],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
