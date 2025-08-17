import json
from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import MessagesState
from src.layers.business_layer.ai_agents.tools.insert_ingestion_args_into_database_tool import (
    InsertIngestionArgsIntoDatabaseTool,
)
from langchain_core.tools import BaseTool, InjectedToolCallId

from typing import Type
from pydantic import BaseModel, Field
from langgraph.types import Command
from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.messages import ToolMessage


class DataIngestionHandoffToolInput(BaseModel):
    task_description: Annotated[
        str,
        Field(
            description="Description of what the next agent should do, including all of the relevant context."
        ),
    ]
    state: Annotated[MessagesState, InjectedState] = Field(
        ..., description="Current state of messages."
    )
    tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


class DataIngestionHandoffTool(BaseTool):
    name: str = "handoff_tool"
    description: str | None = (
        "Hands off a task to another agent with a description and relevant context."
    )
    agent_name: str
    insert_tool: InsertIngestionArgsIntoDatabaseTool | None = None
    args_schema: Type[BaseModel] = DataIngestionHandoffToolInput

    def __init__(
        self,
        agent_name: str,
        insert_tool: InsertIngestionArgsIntoDatabaseTool | None = None,
        description: str | None = None,
    ):
        super().__init__(agent_name=agent_name, insert_tool=insert_tool)
        self.name = f"transfer_to_{agent_name}"
        self.agent_name = agent_name
        self.insert_tool = insert_tool
        self.description = description or f"Ask {agent_name} for help."

    async def _arun(
        self,
        task_description: str,
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        logger.info(f"Executing handoff to {self.agent_name}...")
        if self.agent_name == "inserting_agent":
            logger.info("Handoff to inserting agent detected. Searching for context...")
            ingestion_args_list = list()
            for message in reversed(state["messages"]):
                if (
                    isinstance(message, ToolMessage)
                    and message.name == "map_csvs_to_ingestion_args_tool"
                ):
                    logger.info(
                        "Found ingestion_args_list data. Extracting and parsing it."
                    )
                    try:
                        tooloutput = ToolOutput.from_tool_message(
                            content=message.content
                        )
                        ingestion_args_list = json.loads(tooloutput.result)
                        logger.info(f"ingestion_args_list: {ingestion_args_list}")
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.error(f"Failed to parse ingestion_args: {e}")
                        ingestion_args_list = list()
                    break

            # Instead of a handoff, call the tool directly.
            if ingestion_args_list:
                logger.info(
                    "Calling insert_ingestion_args_into_database_tool directly."
                )
                # We are bypassing the LLM agent entirely for the insertion step.
                return await self.insert_tool._arun(
                    ingestion_args_list=ingestion_args_list
                )
            else:
                message = "Error: Ingestion arguments not found. Handoff failed."
                logger.error(message)
                return ToolMessage(
                    content=message,
                    name=self.name,
                    tool_call_id=tool_call_id,
                )

        tool_message = ToolMessage(
            content=f"Handoff to {self.agent_name} complete. New task assigned.",
            name=self.name,
            tool_call_id=tool_call_id,
        )

        logger.info(f"Final task description for next agent: {task_description}")
        return Command(
            goto=self.agent_name,
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
                description="Description of what the next agent should do, including all of the relevant context."
            ),
        ],
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        message = "Warning: Synchronous execution is not supported. Use _arun instead."
        logger.warning(message)
        raise NotImplementedError(message)
