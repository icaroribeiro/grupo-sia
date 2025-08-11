# from typing import Type
# from pydantic import BaseModel, Field
# from langchain_core.tools import BaseTool
# from src.layers.core_logic_layer.logging import logger
# from langgraph.graph import MessagesState
# from langgraph.types import Command
# from langgraph.types import Send
# from typing import Annotated
# from langchain_core.tools import InjectedToolCallId
# from langgraph.prebuilt import InjectedState
# from langchain_core.messages import ToolMessage


# class HandoffToolInput(BaseModel):
#     task_description: Annotated[
#         str,
#         Field(
#             description="Description of what the next agent should do, including all of the relevant context."
#         ),
#     ]
#     state: Annotated[MessagesState, InjectedState] = Field(
#         ..., description="Current state of messages."
#     )
#     tool_call_id: Annotated[str, InjectedToolCallId] = Field(...)


# class HandoffTool(BaseTool):
#     name: str = "handoff_tool"
#     description: str | None = (
#         "Hands off a task to another agent with a description and relevant context."
#     )
#     agent_name: str
#     args_schema: Type[BaseModel] = HandoffToolInput

#     def __init__(self, agent_name: str, description: str | None = None):
#         super().__init__(
#             agent_name=agent_name,
#         )
#         self.name = f"transfer_to_{agent_name}"
#         self.agent_name = agent_name
#         self.description = description or f"Ask {agent_name} for help."

#     def _run(
#         self,
#         task_description: Annotated[
#             str,
#             Field(
#                 description="Description of what the next agent should do, including all of the relevant context."
#             ),
#         ],
#         state: Annotated[MessagesState, InjectedState],
#         tool_call_id: Annotated[str, InjectedToolCallId],
#     ) -> ToolMessage:
#         logger.info(f"Calling {self.name}...")
#         try:
#             print(f" ---> task_description: {task_description}\n\n")
#             print(f" ---> state: {state}\n\n")

#             # Prepare input for the target agent
#             task_description_message = {"role": "user", "content": task_description}
#             agent_input = {
#                 "messages": state.get("messages", []) + [task_description_message],
#                 "task_description": task_description,
#                 "tool_call_id": tool_call_id,
#             }
#             print(f" ---> agent_input: {agent_input}\n\n")

#             # Create Command for graph navigation
#             command = Command(
#                 goto=[Send(node=self.agent_name, arg=agent_input)],
#                 update={
#                     **state,
#                     "messages": state.get("messages", [])
#                     + [
#                         ToolMessage(
#                             content=f"Successfully transferred to {self.agent_name}",
#                             name=self.name,
#                             tool_call_id=tool_call_id,
#                         )
#                     ],
#                 },
#                 graph=Command.PARENT,
#             )
#             logger.info(f" ---> Command: {command}\n\n")

#             # Create and return ToolMessage with Command embedded in content
#             tool_message = ToolMessage(
#                 content=f"Transferred to {self.agent_name} with command: {command}",
#                 name=self.name,
#                 tool_call_id=tool_call_id,
#             )
#             print(f" ---> tool_message: {tool_message}\n\n")
#             return tool_message
#         except Exception as error:
#             message = f"Error: {str(error)}"
#             logger.error(message)
#             raise

#     async def _arun(
#         self,
#         task_description: Annotated[
#             str,
#             Field(
#                 description="Description of what the next agent should do, including all of the relevant context."
#             ),
#         ],
#         state: Annotated[MessagesState, InjectedState],
#         tool_call_id: Annotated[str, InjectedToolCallId],
#     ) -> ToolMessage:
#         return self._run(
#             task_description=task_description, state=state, tool_call_id=tool_call_id
#         )


# class HandoffToolInput2(BaseModel):
#     task_description: str = Field(
#         ...,
#         description="Description of what the next agent should do, including all of the relevant context.",
#     )
#     tool_call_id: Annotated[str, InjectedToolCallId]
#     state: Annotated[MessagesState, InjectedState]


# class HandoffTool2(BaseTool):
#     name: str = "handoff_tool"
#     description: str | None = (
#         "Hands off a task to another agent with a description and relevant context."
#     )
#     agent_name: str
#     args_schema: Type[BaseModel] = HandoffToolInput2

#     def __init__(self, agent_name: str, description: str | None = None):
#         super().__init__(
#             agent_name=agent_name,
#         )
#         self.name = f"transfer_to_{agent_name}"
#         self.agent_name = agent_name
#         self.description = description or f"Ask {agent_name} for help."

#     def _run(
#         self,
#         state: Annotated[MessagesState, InjectedState],
#         tool_call_id: Annotated[str, InjectedToolCallId],
#     ) -> Command:
#         logger.info(f"Calling {self.name}...")
#         try:
#             print(f" ---> init state: {state}\n\n")
#             task_description_message = {"role": "user", "content": task_description}
#             tool_message = {
#                 "role": "tool",
#                 "content": f"Successfully transferred to {self.agent_name}",
#                 "name": self.name,
#                 "tool_call_id": tool_call_id,
#             }
#             agent_input = {
#                 **state,
#                 "messages": [task_description_message] + [tool_message],
#             }
#             print(f" ---> agent_input: {agent_input}\n\n")
#             result = Command(
#                 goto=[Send(node=self.agent_name, arg=agent_input)],
#                 graph=Command.PARENT,
#             )
#             logger.info(f"Command created: {result}")
#             return result
#         except Exception as error:
#             message = f"Error: {str(error)}"
#             logger.error(message)
#             raise

#     async def _arun(
#         self,
#         task_description: str,
#         tool_call_id: Annotated[str, InjectedToolCallId],
#         state: Annotated[MessagesState, InjectedState],
#     ) -> Command:
#         return self._run(
#             task_description=task_description, tool_call_id=tool_call_id, state=state
#         )
