from typing import Annotated, Type

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class TopLevelHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next workflow should do, including all of the relevant context."
        ),
    ]
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class TopLevelHandoffTool(BaseTool):
    name: str = "top_level_handoff_tool"
    description: str = (
        "Hands off a task to another workflow with a description and relevant context."
    )
    workflow_name: str
    args_schema: Type[BaseModel] = TopLevelHandoffToolInput

    def __init__(
        self,
        workflow_name: str,
    ):
        super().__init__(workflow_name=workflow_name)
        self.name = f"delegate_to_{workflow_name}"
        self.workflow_name = workflow_name

    async def _arun(
        self,
        task_description: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        logger.info(f"Executing handoff to {self.workflow_name}...")
        logger.info(f"Task description for next workflow: {task_description}")
        return ToolMessage(
            content=f"delegate_to_workflow={self.workflow_name}::task={task_description}",
            name=self.name,
            tool_call_id=tool_call_id,
        )

    def _run(
        self,
        task_description: Annotated[
            str,
            Field(
                description="Description of what the next team should do, including all of the relevant context."
            ),
        ],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
