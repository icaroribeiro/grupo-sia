from typing import Annotated, Type

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class DataAnalysisHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next agent should do, including all of the relevant context."
        ),
    ]
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(default=...)


class DataAnalysisHandoffTool(BaseTool):
    name: str = "data_analysis_handoff_tool"
    description: str = (
        "Hands off a task to another agent with a description and relevant context."
    )
    agent_name: str
    args_schema: Type[BaseModel] = DataAnalysisHandoffToolInput

    def __init__(self, agent_name: str):
        super().__init__(agent_name=agent_name)
        self.name = f"delegate_to_{agent_name}_tool"
        self.agent_name = agent_name

    async def _arun(
        self,
        task_description: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        logger.info(f"Executing handoff to {self.agent_name}...")
        logger.info(f"Task description for next agent: {task_description}")
        return ToolMessage(
            content=f"delegate_to={self.agent_name}::task={task_description}",
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
