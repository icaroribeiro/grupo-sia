from src.layers.core_logic_layer.logging import logger
from langchain_core.tools import BaseTool, InjectedToolCallId
from langgraph.types import Command
from typing import Type
from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState


class MealVoucherCalculationHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next node should do, including all of the relevant context."
        ),
    ]
    state: Annotated[dict, InjectedState]
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class MealVoucherCalculationHandoffTool(BaseTool):
    name: str = "handoff_tool"
    description: str | None = (
        "Hands off a task to another node with a description and relevant context."
    )
    node_name: str
    args_schema: Type[BaseModel] = MealVoucherCalculationHandoffToolInput

    def __init__(
        self,
        node_name: str,
        description: str | None = None,
    ):
        super().__init__(node_name=node_name)
        self.name = f"transfer_to_{node_name}"
        self.node_name = node_name
        self.description = description or f"Ask {node_name} for help."

    async def _arun(
        self,
        task_description: str,
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        logger.info(f"Executing handoff to {self.node_name}...")
        logger.info(f"Task description for next node: {task_description}")
        tool_message = ToolMessage(
            content=f"Handoff to {self.node_name} complete. New task assigned.",
            name=self.name,
            tool_call_id=tool_call_id,
        )
        return Command(
            goto=self.node_name,
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
                description="Description of what the next node should do, including all of the relevant context."
            ),
        ],
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
