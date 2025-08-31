from typing import Annotated, Type

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId
from langgraph.graph import MessagesState
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.layers.core_logic_layer.logging import logger


class TopLevelHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next team should do, including all of the relevant context."
        ),
    ]
    state: Annotated[MessagesState, InjectedState] = Field(
        ..., description="Current state of messages."
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class TopLevelHandoffTool(BaseTool):
    name: str = "handoff_tool"
    description: str | None = (
        "Hands off a task to another team with a description and relevant context."
    )
    team_name: str
    args_schema: Type[BaseModel] = TopLevelHandoffToolInput

    def __init__(
        self,
        team_name: str,
        description: str | None = None,
    ):
        super().__init__(team_name=team_name)
        self.name = f"transfer_to_{team_name}"
        self.team_name = team_name
        self.description = description or f"Ask {team_name} for help."

    async def _arun(
        self,
        task_description: str,
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        logger.info(f"Executing handoff to {self.team_name}...")
        tool_message = ToolMessage(
            content=f"Handoff to {self.team_name} complete. New task assigned.",
            name=self.name,
            tool_call_id=tool_call_id,
        )
        logger.info(f"Task description for next team: {task_description}")
        return Command(
            goto=self.team_name,
            graph=Command.PARENT,
            update={
                "messages": state["messages"] + [tool_message],
                "task_description": task_description,
            },
        )

    def _run(
        self,
        task_description: Annotated[
            str,
            Field(
                description="Description of what the next team should do, including all of the relevant context."
            ),
        ],
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
