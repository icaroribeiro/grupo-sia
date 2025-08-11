import json
import uuid
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor
from src.layers.business_layer.ai_agents.tools.insert_ingestion_args_into_database_tool import (
    InsertIngestionArgsIntoDatabaseTool,
)
from langchain_core.tools import BaseTool, InjectedToolCallId
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langgraph.prebuilt import create_react_agent

from typing import Type
from pydantic import BaseModel, Field
from langgraph.types import Command
from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.messages import ToolMessage


class HandoffToolInput(BaseModel):
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


class HandoffTool(BaseTool):
    name: str = "handoff_tool"
    description: str | None = (
        "Hands off a task to another agent with a description and relevant context."
    )
    agent_name: str
    args_schema: Type[BaseModel] = HandoffToolInput

    def __init__(
        self,
        agent_name: str,
        description: str | None = None,
    ):
        super().__init__(
            agent_name=agent_name,
        )
        self.name = f"transfer_to_{agent_name}"
        self.agent_name = agent_name
        self.description = description or f"Ask {agent_name} for help."

    def _run(
        self,
        task_description: str,
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> ToolMessage:
        logger.info(f"Executing handoff to {self.agent_name}...")

        ingestion_args_data = None

        if self.agent_name == "ingestion_args_inserter_agent":
            logger.info(
                "Handoff to inserter detected. Searching for ingestion_args context..."
            )
            for message in reversed(state["messages"]):
                if (
                    isinstance(message, ToolMessage)
                    and message.name == "map_csvs_to_ingestion_args_tool"
                ):
                    logger.info(
                        "Found ingestion_args data. Extracting and cleaning it."
                    )
                    try:
                        ingestion_args_str = message.content.replace(
                            "ingestion_args=", "", 1
                        )
                        ingestion_args_data = json.loads(ingestion_args_str)
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.error(f"Failed to parse ingestion_args: {e}")
                        ingestion_args_data = []  # Fallback to empty list
                    break

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
                "ingestion_args": ingestion_args_data,
            },
        )

    async def _arun(
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
        return self._run(
            task_description=task_description, state=state, tool_call_id=tool_call_id
        )


class HandoffTool2(BaseTool):
    name: str = "handoff_tool"
    description: str | None = (
        "Hands off a task to another agent with a description and relevant context."
    )
    agent_name: str
    insert_tool: InsertIngestionArgsIntoDatabaseTool | None = None
    args_schema: Type[BaseModel] = HandoffToolInput

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

        ingestion_args_data = None

        if self.agent_name == "ingestion_args_inserter_agent":
            logger.info(
                "Handoff to inserter detected. Searching for ingestion_args context..."
            )
            for message in reversed(state["messages"]):
                if (
                    isinstance(message, ToolMessage)
                    and message.name == "map_csvs_to_ingestion_args_tool"
                ):
                    logger.info("Found ingestion_args data. Extracting and parsing it.")
                    try:
                        ingestion_args_str = message.content.replace(
                            "ingestion_args=", "", 1
                        )
                        # The json.loads is correct, it produces the Python list you want.
                        ingestion_args_data = json.loads(ingestion_args_str)
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.error(f"Failed to parse ingestion_args: {e}")
                        ingestion_args_data = []  # Fallback to empty list
                    break

            # CRITICAL CHANGE: Instead of a handoff, call the tool directly.
            if ingestion_args_data:
                logger.info(
                    "Calling insert_ingestion_args_into_database_tool directly."
                )
                # We are bypassing the LLM agent entirely for the insertion step.
                return await self.insert_tool._arun(ingestion_args=ingestion_args_data)
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


class DatabaseIngestionWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
    ):
        self.name = "database_ingestion_workflow"
        self.chat_model = chat_model
        self.file_unzipper_agent = create_react_agent(
            model=self.chat_model,
            tools=[unzip_files_from_zip_archive_tool],
            prompt=(
                """
                ROLE:
                You're a file unzipper agent.
                GOAL:
                Your sole purpose is to unzip files. DO NOT perform any other tasks.
                INSTRUCTIONS:
                After you're done, respond to the supervisor with the file paths of the unzipped files.
                CRITICAL RULES:
                Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.
                """
            ),
            name="file_unzipper_agent",
        )
        self.csv_mapping_agent = create_react_agent(
            model=self.chat_model,
            tools=[map_csvs_to_ingestion_args_tool],
            prompt=(
                """
                ROLE:
                You're csv mapping agent.
                GOAL:
                Your sole purpose is to map csv file. DO NOT perform any other tasks.
                INSTRUCTIONS:
                After you're done, respond to the supervisor with the ingestion arguments.
                CRITICAL RULES:
                Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.
                """
            ),
            name="csv_mapping_agent",
        )
        self.ingestion_args_inserter_agent = create_react_agent(
            model=self.chat_model,
            tools=[insert_ingestion_args_into_database_tool],
            prompt=(
                """
                PROFILE:
                You're an ingestion arguments inserter agent.
                GOAL:
                Your sole purpose is to insert ingestion arguments. DO NOT perform any other tasks.
                INSTRUCTIONS:
                The data you need for this task is available in your current state: a state variable named `ingestion_args`.
                You MUST access this state variable `ingestion_args` and provide its ENTIRE contents to the `insert_ingestion_args_into_database_tool` in a single call.
                After you're done, respond to the supervisor with the number of inserted items.
                CRITICAL RULES:
                DO NOT attempt to parse or reconstruct the content of state variable.
                NEVER change the content of state variable when sending it to the `insert_ingestion_args_into_database_tool`.
                Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.
                """
            ),
            name="ingestion_args_inserter_agent",
        )
        # assign_to_file_unzipper_agent = create_custom_handoff_tool(
        #     agent_name=self.file_unzipper_agent.name,
        #     name=f"assign_to_{self.file_unzipper_agent.name}",
        #     description=f"Assign task to {self.file_unzipper_agent.name}",
        # )
        # assign_to_csv_mapping_agent = create_custom_handoff_tool(
        #     agent_name=self.csv_mapping_agent.name,
        #     name=f"assign_to_{self.csv_mapping_agent.name}",
        #     description=f"Assign task to {self.csv_mapping_agent.name}",
        # )
        # assign_to_ingestion_args_inserter_agent = create_custom_handoff_tool(
        #     agent_name=self.ingestion_args_inserter_agent.name,
        #     name=f"assign_to_{self.ingestion_args_inserter_agent.name}",
        #     description=f"Assign task to {self.ingestion_args_inserter_agent.name}",
        # )
        # assign_to_file_unzipper_agent = HandoffTool2(
        #     agent_name=self.file_unzipper_agent.name,
        # )
        # assign_to_csv_mapping_agent = HandoffTool2(
        #     agent_name=self.csv_mapping_agent.name,
        # )
        # assign_to_ingestion_args_inserter_agent = HandoffTool2(
        #     agent_name=self.ingestion_args_inserter_agent.name,
        # )
        assign_to_file_unzipper_agent = HandoffTool(
            agent_name=self.file_unzipper_agent.name,
        )
        assign_to_csv_mapping_agent = HandoffTool(
            agent_name=self.csv_mapping_agent.name,
        )
        assign_to_ingestion_args_inserter_agent = HandoffTool(
            agent_name=self.ingestion_args_inserter_agent.name,
        )
        self.supervisor = create_react_agent(
            model=self.chat_model,
            tools=[
                assign_to_file_unzipper_agent,
                assign_to_csv_mapping_agent,
                assign_to_ingestion_args_inserter_agent,
            ],
            prompt=(
                """
                ROLE:
                You're a supervisor."
                GOAL:
                Your sole purpose is to manage three agents:"
                - A file unzipping agent. Assign unzip file-related tasks to this agent.
                - A csv mapping agent. Assign map csv-related tasks to this agent.
                - An ingestion arguments inserter agent. Assign insert ingestion-arguments-related tasks to this agent.
                INSTRUCTIONS:
                Based on the conversation history, decide the next step.
                DO NOT do any work yourself.
                CRITICAL RULES:
                ALWAYS assign work to one agent at a time, DO NOT call agents in parallel.
                """
            ),
            name="supervisor",
        )
        self.__graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)
        builder.add_node(
            self.supervisor,
            destinations=(
                self.file_unzipper_agent.name,
                self.csv_mapping_agent.name,
                self.ingestion_args_inserter_agent.name,
            ),
        )
        builder.add_node(self.file_unzipper_agent)
        builder.add_node(self.csv_mapping_agent)
        builder.add_node(self.ingestion_args_inserter_agent)
        builder.add_edge(START, self.supervisor.name)
        builder.add_edge(self.file_unzipper_agent.name, self.supervisor.name)
        builder.add_edge(self.csv_mapping_agent.name, self.supervisor.name)
        builder.add_edge(self.ingestion_args_inserter_agent.name, self.supervisor.name)
        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(self, input_message: str) -> dict:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

        async for chunk in self.__graph.astream(
            input_state,
            subgraphs=True,
            config={"configurable": {"thread_id": thread_id}},
        ):
            self._pretty_print_messages(chunk, last_message=True)
        result = chunk[1]["supervisor"]["messages"]
        # for message in result:
        #     message.pretty_print()
        # result = await self.__graph.ainvoke(
        #     input_state,
        #     config={"configurable": {"thread_id": thread_id}},
        # )
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result


class DatabaseIngestionWorkflow2(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
    ):
        self.name = "database_ingestion_workflow"
        self.chat_model = chat_model
        self.file_unzipper_agent = create_react_agent(
            model=self.chat_model,
            tools=[unzip_files_from_zip_archive_tool],
            prompt=(
                """
                PROFILE:\n
                You're a file unzipper agent.\n\n

                BACKSTORY:\n
                - Your sole purpose is to unzip files. DO NOT perform any other tasks.
                - After you're done, respond to the supervisor with the file paths of the unzipped files.
                - Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.\n
                """
            ),
            name="file_unzipper_agent",
        )
        self.csv_mapping_agent = create_react_agent(
            model=self.chat_model,
            tools=[map_csvs_to_ingestion_args_tool],
            prompt=(
                """
                PROFILE:\n
                You're csv mapping agent.\n\n

                BACKSTORY:\n
                - Your sole purpose is to map csv file. DO NOT perform any other tasks.
                - After you're done, respond to the supervisor with the ingestion arguments.
                - Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.\n
                """
            ),
            name="csv_mapping_agent",
        )
        self.ingestion_args_inserter_agent = create_react_agent(
            model=self.chat_model,
            tools=[insert_ingestion_args_into_database_tool],
            prompt=(
                """
                PROFILE:\n
                You're an ingestion arguments inserter agent.\n\n

                BACKSTORY:\n
                - Your sole purpose is to insert ingest arguments. DO NOT perform any other tasks.
                - After you're done, respond to the supervisor with the number of inserted items.
                - Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.\n
                """
            ),
            name="ingestion_args_inserter_agent",
        )
        self.supervisor = create_supervisor(
            model=self.chat_model,
            agents=[
                self.file_unzipper_agent,
                self.csv_mapping_agent,
                self.ingestion_args_inserter_agent,
            ],
            tools=[
                # create_handoff_tool(
                #     agent_name=self.file_unzipper_agent.name,
                #     name=f"assign_to_{self.file_unzipper_agent.name}",
                #     description=f"Assign task to {self.file_unzipper_agent.name}",
                # ),
                # create_handoff_tool(
                #     agent_name=self.csv_mapping_agent.name,
                #     name=f"assign_to_{self.csv_mapping_agent.name}",
                #     description=f"Assign task to {self.csv_mapping_agent.name}",
                # ),
                # create_handoff_tool(
                #     agent_name=self.ingestion_args_inserter_agent.name,
                #     name=f"assign_to_{self.ingestion_args_inserter_agent.name}",
                #     description=f"Assign task to {self.ingestion_args_inserter_agent.name}",
                # ),
                HandoffTool(agent_name=self.file_unzipper_agent.name),
                HandoffTool(agent_name=self.csv_mapping_agent.name),
                HandoffTool(agent_name=self.ingestion_args_inserter_agent.name),
            ],
            prompt=(
                """
                PROFILE:\n
                You're a supervisor managing three agents:\n"
                - A file unzipping agent. Assign unzip file-related tasks to this agent\n
                - A csv mapping agent. Assign map csv-related tasks to this agent\n
                - An ingestion arguments inserter agent. Assign insert ingestion-arguments-related tasks to this agent\n
                
                BACKSTORY:\n
                - DO NOT do any work yourself\n
                - ALWAYS assign work to one agent at a time, DO NOT call agents in parallel\n
                """
            ),
            add_handoff_back_messages=True,
            output_mode="full_history",
        )
        self.__graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = self.supervisor.compile(
            name=self.name, checkpointer=InMemorySaver(), store=InMemoryStore()
        )
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(self, input_message: str) -> dict:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

        async for chunk in self.__graph.astream(
            input_state,
            subgraphs=True,
            config={"configurable": {"thread_id": thread_id}},
        ):
            self._pretty_print_messages(chunk, last_message=True)
        result = chunk[1]["supervisor"]["messages"]
        # for message in result:
        #     message.pretty_print()
        # result = await self.__graph.ainvoke(
        #     input_state,
        #     config={"configurable": {"thread_id": thread_id}},
        # )
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result


# def create_custom_handoff_tool(
#     *, agent_name: str, name: str | None, description: str | None
# ) -> BaseTool:
#     @tool(name, description=description)
#     def handoff_to_agent(
#         # you can add additional tool call arguments for the LLM to populate
#         # for example, you can ask the LLM to populate a task description for the next agent
#         task_description: Annotated[
#             str,
#             "Detailed description of what the next agent should do, including all of the relevant context.",
#         ],
#         # you can inject the state of the agent that is calling the tool
#         state: Annotated[dict, InjectedState],
#         tool_call_id: Annotated[str, InjectedToolCallId],
#     ):
#         tool_message = ToolMessage(
#             content=f"Successfully transferred to {agent_name}",
#             name=name,
#             tool_call_id=tool_call_id,
#         )
#         messages = state["messages"]
#         return Command(
#             goto=agent_name,
#             graph=Command.PARENT,
#             # NOTE: this is a state update that will be applied to the swarm multi-agent graph (i.e., the PARENT graph)
#             update={
#                 "messages": messages + [tool_message],
#                 "active_agent": agent_name,
#                 # optionally pass the task description to the next agent
#                 # NOTE: individual agents would need to have `task_description` in their state schema
#                 # and would need to implement logic for how to consume it
#                 "task_description": task_description,
#             },
#         )

#     handoff_to_agent.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
#     return handoff_to_agent


###########

# def __call_supervisor(self, state: WorkflowState):
#         logger.info(f"Calling {self.supervisor_agent.name}...")
#         messages = state["messages"]

#         # if (
#         #     messages
#         #     and isinstance(messages[-1], AIMessage)
#         #     and messages[-1].content
#         # ):
#         #     # If the last message is a content-ful AIMessage (not a tool call),
#         #     # we assume this is the final answer and route to FINISH.
#         #     if not (
#         #         hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls
#         #     ):
#         #         logger.info("Supervisor found final answer. Routing to: FINISH")
#         #         return {"next": "FINISH"}

#         assistant_names = self.assistant_names
#         assistant_names_str = ", ".join(assistant_names)
#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     """
#                     You are a team supervisor routing tasks between the following assistants:
#                     {assistant_names_str}.
#                     - `assistant_1` is a specialist in unzipping files.
#                     - `assistant_2` is a specialist in reading the content of files.

#                     **Here are your CRITICAL instructions:**
#                     1. Your primary goal is to ensure the user's request is fully completed.
#                     2. Analyze the user request and the entire conversation history.
#                     3. Your task is to determine the NEXT step.

#                     **Routing Logic:**
#                     - If the **last message in the conversation** is a final, conclusive answer to the user's original request, route to FINISH.
#                     A final answer will be a human-readable message, not a tool-calling message or a tool output.
#                     - If the task requires a new action or a different assistant to proceed, route to the appropriate assistant.
#                     For example, if files have just been unzipped by `assistant_1`, and the user wants to know what's inside them, you should route to `assistant_2`.

#                     Respond with a JSON object with a single key 'next' mapping to one of [{assistant_names_str}, FINISH] as follows:
#                     ```json
#                         {{"next": "<next_node>"}}
#                     ```
#                     where <next_node> is the node to route to (e.g., {entry_node} or {finish_node}).
#                     """,
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         ).partial(
#             assistant_names_str=assistant_names_str,
#             finish_node="FINISH",
#             entry_node=self.assistant_names[0],
#         )
#         chain = prompt | self.llm | JsonOutputParser()
#         response = chain.invoke({"messages": messages})
#         logger.info(f"{self.supervisor.name} routing to: {response['next']}")
#         return {"next": response["next"]}

#     def __call_assistant_1(self, state: WorkflowState):
#         logger.info(f"Calling {self.assistant_1.name}...")
#         messages = state["messages"]
#         logger.info(f"messages: {messages}")
#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     """
#                     You are an unzip file specialist.
#                     - If asked to unzip a file, call the `UnzipFilesFromZipArchiveTool` immediately.
#                     - If you receive a `ToolMessage` with the result, summarize it to confirm the task is done."
#                     """,
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         )
#         llm_with_tools = self.llm.bind_tools(self.assistant_1.tools)
#         chain = prompt | llm_with_tools
#         response = chain.invoke({"messages": messages})

#         # The agent's response is the key to routing.
#         # We don't need to return 'next' here, the conditional edge will handle it.
#         # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
#         return {"messages": [response], "sender": self.assistant_1.name}

#     def __call_assistant_2(self, state: WorkflowState):
#         logger.info(f"Calling {self.assistant_2.name}...")
#         messages = state["messages"]
#         logger.info(f"messages: {messages}")
#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     """
#                     You are a file reading specialist.
#                     - The user will ask you to read a file whose path was likely provided by `assistant_1`.
#                     - Look at the conversation history to find the file paths. Call the `ReadFileTool` to read the content of a file.
#                     - If you receive a `ToolMessage` from `ReadFileTool`, its output is an object with a 'result' field containing the file's content.
#                     - Your final answer should be a summary of this content. For example: "I have read the file. The content begins with: [first 100 characters of content]".
#                     """,
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         )
#         llm_with_tools = self.llm.bind_tools(self.assistant_2.tools)
#         chain = prompt | llm_with_tools
#         response = chain.invoke({"messages": messages})

#         # The agent's response is the key to routing.
#         # We don't need to return 'next' here, the conditional edge will handle it.
#         # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
#         return {"messages": [response], "sender": self.assistant_2.name}

#     def __route_from_supervisor(self, state: WorkflowState):
#         logger.info(f"Routing from {self.supervisor.name}...")
#         next_node = state["next"]
#         logger.info(f"Routing decision: '{next_node}'")
#         return next_node

#     def __route_from_assistant(self, state: WorkflowState):
#         logger.info(f"Routing from {self.assistant_1.name}...")
#         last_message = state["messages"][-1]
#         logger.info(f"Last message content: {last_message.content}")
#         logger.info(
#             f"Tool calls found: {hasattr(last_message, 'tool_calls') and last_message.tool_calls}"
#         )

#         # If there are tool calls, go to the tools node.
#         if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#             logger.info("Routing decision: 'tools' (tool calls found)")
#             return "tools"
#         # If the LLM has provided a final answer, route back to the supervisor to finish.
#         elif hasattr(last_message, "content") and last_message.content:
#             logger.info(
#                 f"Routing decision: '{self.supervisor.name}' (final content found)"
#             )
#             return self.supervisor.name
#         # Otherwise, something went wrong, and we should probably route back to the supervisor
#         # or have a more robust error handling mechanism. For now, we'll route to supervisor.
#         else:
#             logger.warning(
#                 f"Routing decision: '{self.supervisor.name}' (no tool calls or final content)"
#             )
#             return self.supervisor.name

#     def __route_from_tools(self, state: WorkflowState):
#         logger.info("Routing from tools back to...")
#         next_node = state["sender"]
#         logger.info(f"Routing decision: '{next_node}'")
#         return next_node

###########

# import os
# import re
# import uuid
# import zipfile
# from typing import Annotated, Any, Sequence, Type, TypedDict

# import pandas as pd
# from langchain_core.language_models import BaseChatModel
# from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.tools import BaseTool
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import END, StateGraph
# from langgraph.graph.message import add_messages
# from pydantic import BaseModel, ConfigDict, Field
# from sqlalchemy.exc import IntegrityError

# from src.layers.business_layer.ai_agents.models.invoice_item_model import (
#     InvoiceItemModel,
# )
# from src.layers.business_layer.ai_agents.models.invoice_model import InvoiceModel
# from src.layers.core_logic_layer.logging import logger
# from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
#     InvoiceItemModel as SQLAlchemyInvoiceItemModel,
# )
# from src.layers.data_access_layer.postgresdb.models.invoice_model import (
#     InvoiceModel as SQLAlchemyInvoiceModel,
# )
# from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


# # --- Pydantic model definitions with the fix ---
# class InvoiceIngestionConfig(BaseModel):
#     table_name: str = Field(default="invoice", description="Database table name.")
#     model: InvoiceModel = Field(..., description="Pydantic InvoiceModel class.")


# class InvoiceItemIngestionConfig(BaseModel):
#     table_name: str = Field(default="invoice_item", description="Database table name.")
#     model: InvoiceItemModel = Field(..., description="Pydantic InvoiceItemModel class.")


# class ToolOutput(BaseModel):
#     message: str = ""
#     result: Any = None

#     model_config = ConfigDict(arbitrary_types_allowed=True)


# class WorkflowState(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], add_messages]
#     next: str
#     tool_output: ToolOutput


# class UnzipFilesFromZipArchiveInput(BaseModel):
#     """Input schema for UnzipFilesFromZipArchiveTool."""

#     file_path: str = Field(..., description="Path to the ZIP file.")
#     destination_dir_path: str = Field(
#         ..., description="Path to the destination directory."
#     )


# class UnzipFilesFromZipArchiveTool(BaseTool):
#     name: str = "unzip_files_from_zip_archive_tool"
#     description: str = """
#     Unzip files from ZIP archive to a destination directory.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (list of paths of extracted files from ZIP archive on success or empty list on failure).
#     """
#     args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

#     def _run(self, file_path: str, destination_dir_path: str) -> ToolOutput:
#         logger.info("The UnzipFilesFromZipArchiveTool call has started...")
#         try:
#             # Ensure the destination directory exists
#             os.makedirs(destination_dir_path, exist_ok=True)

#             # List to store extracted file paths
#             extracted_files = []

#             # Unzip the file
#             with zipfile.ZipFile(file_path, "r") as zip_ref:
#                 zip_ref.extractall(destination_dir_path)
#                 # Get the list of extracted files
#                 extracted_files = [
#                     os.path.join(destination_dir_path, name)
#                     for name in zip_ref.namelist()
#                     if not name.endswith("/")
#                 ]

#             # Normalize file paths to use forward slashes
#             extracted_files = [file.replace("\\", "/") for file in extracted_files]

#             message = f"Success: ZIP file {file_path} extracted"
#             logger.info(f"{message}: {','.join(extracted_files)}")
#             logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
#             return ToolOutput(message=message, result=extracted_files)

#         except Exception as e:
#             message = f"Error unzipping file {file_path}: {str(e)}"
#             logger.error(message)
#             logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
#             return ToolOutput(message=message, result=[])

#     async def _arun(self, file_path: str, destination_dir_path: str) -> ToolOutput:
#         return self._run(file_path=file_path, destination_dir_path=destination_dir_path)


# class MapCSVsToIngestionArgsInput(BaseModel):
#     """Input schema for MapCSVsToIngestionArgsTool."""

#     file_paths: list[str] = Field(
#         ..., description="List of paths of extracted CSV files."
#     )


# class MapCSVsToIngestionArgsTool(BaseTool):
#     name: str = "map_csvs_to_ingestion_args_tool"
#     description: str = """
#     Map a list of paths of extracted CSV files to a dictionary of lists of ingestion arguments.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (dictionary with integer keys and lists of ingestion arguments on success or None on failure.)
#     """
#     args_schema: Type[BaseModel] = MapCSVsToIngestionArgsInput

#     def _run(self, file_paths: list[str]) -> ToolOutput:
#         logger.info("The MapCSVsToIngestionArgsTool call has started...")
#         suffix_to_args: dict[
#             tuple[int, str],
#             tuple[
#                 InvoiceIngestionConfig | InvoiceItemIngestionConfig,
#                 InvoiceModel | InvoiceItemModel,
#             ],
#         ] = {
#             (0, "NFe_NotaFiscal"): (InvoiceIngestionConfig, InvoiceModel),
#             (1, "NFe_NotaFiscalItem"): (InvoiceItemIngestionConfig, InvoiceItemModel),
#         }
#         ingestion_args_dict: dict[
#             int, list[InvoiceIngestionConfig | InvoiceItemIngestionConfig]
#         ] = dict()

#         for file_path in file_paths:
#             file_name = os.path.basename(file_path)
#             for (key, suffix), (args_class, model_class) in suffix_to_args.items():
#                 if ingestion_args_dict.get(key) is None:
#                     ingestion_args_dict[key] = []

#                 if re.match(rf"\d{{6}}_{suffix}\.csv$", file_name):
#                     try:
#                         df = pd.read_csv(
#                             file_path,
#                             encoding="latin1",
#                             sep=";",
#                             dtype=model_class.get_csv_columns_to_dtypes()
#                             if hasattr(model_class, "get_csv_columns_to_dtypes")
#                             else str,
#                         )
#                     except FileNotFoundError as error:
#                         message = f"Error: Failed to find file at {file_path}: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)
#                     except UnicodeDecodeError as error:
#                         message = f"Error: Failed to decode data from file {file_path}: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)
#                     except Exception as error:
#                         message = f"Error: Failed to read file {file_path}: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)

#                     try:
#                         for index, row in df.iterrows():
#                             try:
#                                 model_data = {}
#                                 for (
#                                     csv_col,
#                                     doc_field_info,
#                                 ) in model_class.get_csv_columns_to_model_fields().items():
#                                     field_name = doc_field_info["field"]
#                                     converter = doc_field_info.get("converter")
#                                     value = row.get(csv_col)
#                                     if value is pd.NA or pd.isna(value):
#                                         value = None

#                                     if converter:
#                                         try:
#                                             value = converter(value)
#                                         except ValueError as error:
#                                             message = f"Warning: Could not convert '{value}' for field '{field_name}' in row {index + 1} of {file_path}: {error}"
#                                             logger.warning(message)
#                                             continue
#                                     model_data[field_name] = value
#                                 model = model_class(**model_data)
#                                 ingestion_args_dict[key].append(args_class(model=model))
#                             except Exception as error:
#                                 message = f"Error: Failed to process row {index + 1} from {file_path}: {error}"
#                                 logger.error(message)
#                                 continue
#                         message = f"Success: Models mapped from file {file_path}"
#                     except Exception as error:
#                         message = f"Error: Failed to map ingestion arguments dict {ingestion_args_dict} to models dict: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)

#         serialized_models_dict = {
#             key: [
#                 {
#                     "table_name": ingestion_arg.table_name,
#                     "model": ingestion_arg.model.model_dump(),
#                 }
#                 for ingestion_arg in ingestion_args
#             ]
#             for key, ingestion_args in ingestion_args_dict.items()
#         }

#         logger.info("The MapCSVsToPydanticModelsTool call has finished.")
#         return ToolOutput(message=message, result=serialized_models_dict)

#     async def _arun(self, file_paths: list[str]) -> ToolOutput:
#         return self._run(file_paths=file_paths)


# class InsertIngestionArgsIntoDatabaseInput(BaseModel):
#     """Input schema for InsertIngestionArgsIntoDatabaseTool."""

#     ingestion_args_dict: dict[
#         int, list[InvoiceIngestionConfig | InvoiceItemIngestionConfig]
#     ] = Field(..., description="A dictionary of lists of ingestion arguments.")


# class InsertIngestionArgsIntoDatabaseTool(BaseTool):
#     name: str = "insert_ingestion_args_into_database_tool"
#     description: str = """
#     Insert SQLAlchemy database models into Postgres database.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (total number of inserted records on success or None on failure).
#     """
#     postgresdb: PostgresDB
#     args_schema: Type[BaseModel] = InsertIngestionArgsIntoDatabaseInput

#     def __init__(self, postgresdb: PostgresDB):
#         super().__init__(postgresdb=postgresdb)
#         self.postgresdb = postgresdb

#     async def _arun(
#         self,
#         ingestion_args_dict: dict[int, list[dict[str, Any]]],
#     ) -> ToolOutput:
#         logger.info("The InsertIngestionArgsIntoDatabaseTool call has started...")
#         sqlalchemy_models_dict: dict[
#             int, list[SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel]
#         ] = dict()

#         for key, ingestion_args_list in ingestion_args_dict.items():
#             if sqlalchemy_models_dict.get(key) is None:
#                 sqlalchemy_models_dict[key] = []

#             for ingestion_args in ingestion_args_list:
#                 table_name = ingestion_args["table_name"]
#                 model_class: Type[SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel]
#                 # Replace match with if-elif
#                 if table_name == SQLAlchemyInvoiceModel.get_table_name():
#                     model_class = SQLAlchemyInvoiceModel
#                 elif table_name == SQLAlchemyInvoiceItemModel.get_table_name():
#                     model_class = SQLAlchemyInvoiceItemModel
#                 else:
#                     message = f"Error: Invalid table name {table_name}"
#                     logger.error(message)
#                     return ToolOutput(message=message, result=None)

#                 try:
#                     model = model_class.from_data(data=ingestion_args["model"])
#                     sqlalchemy_models_dict[key].append(model)
#                 except Exception as error:
#                     message = f"Error: Failed to create SQLAlchemy model from args {ingestion_args}: {error}"
#                     logger.error(message)
#                     continue

#         count_map: dict[str, int] = dict()
#         try:
#             async with self.postgresdb.async_session() as async_session:
#                 if len(sqlalchemy_models_dict) > 0:
#                     for _, models in sorted(sqlalchemy_models_dict.items()):
#                         for model in models:
#                             if count_map.get(model.get_table_name(), None) is None:
#                                 count_map[model.get_table_name()] = 0
#                             try:
#                                 async_session.add(model)
#                                 count_map[model.get_table_name()] += 1
#                             except IntegrityError:
#                                 message = f"Warning: Model already exists. Skipping duplicate model: {getattr(model, 'access_key', 'N/A')}"
#                                 logger.warning(message)
#                                 continue
#                             except Exception as error:
#                                 await async_session.rollback()
#                                 message = (
#                                     f"Error: Failed to insert model {model}: {error}"
#                                 )
#                                 logger.error(message)
#                                 return ToolOutput(message=message, result=None)
#                         try:
#                             await async_session.commit()
#                             message = f"Success: All {model.get_table_name()} table records have been committed."
#                             logger.info(message)
#                         except Exception as error:
#                             await async_session.rollback()
#                             message = f"Error: Failed to commit the current transaction: {error}"
#                             logger.error(message)
#                             return ToolOutput(message=message, result=None)
#         except Exception as error:
#             message = f"Error: Failed to establish database connection: {error}"
#             logger.error(message)
#             return ToolOutput(message=message, result=None)

#         if len(count_map) > 0:
#             total_count: int = 0
#             for model_name, count in count_map.items():
#                 total_count += count
#                 message = f"Success: {count} record(s) inserted into {model_name} table"
#                 logger.info(message)
#             message = f"Success: Total of {total_count} record(s) inserted into Postgres database"
#             logger.info("The InsertIngestionArgsIntoDatabaseTool call has finished.")
#             return ToolOutput(message=message, result=total_count)
#         else:
#             message = "Warning: No records to insert into Postgres database."
#             logger.warning(message)
#             return ToolOutput(message=message, result=0)

#     def _run(
#         self,
#         ingestion_args_dict: dict[int, list[dict]],
#     ) -> ToolOutput:
#         message = "Warning: Synchronous execution is not supported. Use _arun instead."
#         logger.warning(message)
#         raise NotImplementedError(message)


# class DataIngestionWorkflow:
#     def __init__(
#         self,
#         llm: BaseChatModel,
#         unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
#         map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
#         insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
#     ):
#         self.__name = "data_ingestion_workflow"
#         self.llm = llm

#         self.unzip_tool = unzip_files_from_zip_archive_tool
#         self.map_csvs_tool = map_csvs_to_ingestion_args_tool
#         self.insert_database_tool = insert_ingestion_args_into_database_tool
#         self.worker_1_tools = [self.unzip_tool]
#         self.worker_2_tools = [self.map_csvs_tool]
#         self.worker_3_tools = [self.insert_database_tool]
#         self.all_tools = self.worker_1_tools + self.worker_2_tools + self.worker_3_tools

#         self.__graph = self._build_graph()

#     def _build_graph(self) -> StateGraph:
#         workflow = StateGraph(state_schema=WorkflowState)

#         # --- 1. Define the Supervisor Node (Router) - UNCHANGED ---
#         def call_supervisor(state: WorkflowState):
#             print("---SUPERVISOR---")
#             messages = state["messages"]
#             worker_names = ["worker_node_1", "worker_node_2", "worker_node_3"]
#             worker_names_str = ", ".join(worker_names)
#             finish_node = '{{"next": "FINISH"}}'
#             entry_node = (
#                 f'{{{{"next": "{worker_names[0]}"}}}}'
#                 if worker_names
#                 else '{{"next": "FINISH"}}'
#             )
#             next_node = '{{"next": "<next_node>"}}'
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         """You are a supervisor routing tasks to workers. Based on the conversation history, decide the next step.
#                         Current available workers: [{worker_names_str}].
#                         Analyze the user request and conversation history to determine
#                         which worker can handle it best.

#                         If the input messages indicate that the task is complete, or if
#                         the state contains 'next': 'FINISH', return {finish_node}.

#                         Respond in the following JSON format:
#                         ```json
#                         {next_node}
#                         ```
#                         where <next_node> is the node to route to (e.g., {entry_node}
#                         or {finish_node}).
#                         """.format(
#                             worker_names_str=worker_names_str,
#                             finish_node=finish_node,
#                             next_node=next_node,
#                             entry_node=entry_node,
#                         ),
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             ).partial(
#                 worker_names_str=", ".join(worker_names_str),
#                 finish_node=finish_node,
#                 next_node=next_node,
#                 entry_node=entry_node,
#             )
#             chain = prompt | self.llm | JsonOutputParser()
#             response = chain.invoke({"messages": messages})
#             print(f"Supervisor routing to: {response['next']}")
#             return {"messages": messages, "next": response["next"]}

#         # --- 2. Define Worker Node 1 (Unzip Task) - UNCHANGED ---
#         def call_worker_node_1(state: WorkflowState):
#             print("---WORKER NODE 1 (UNZIP AGENT)---")
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         "You are an unzip specialist. You have access to a tool to unzip files. Call this tool to start the workflow.",
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             )
#             llm_with_tools = self.llm.bind_tools(self.worker_1_tools)
#             chain = prompt | llm_with_tools
#             response = chain.invoke({"messages": state["messages"]})
#             if hasattr(response, "tool_calls") and response.tool_calls:
#                 seen = set()
#                 unique_tool_calls = []
#                 for tool_call in response.tool_calls:
#                     tool_key = (tool_call["name"], str(tool_call["args"]))
#                     if tool_key not in seen:
#                         seen.add(tool_key)
#                         unique_tool_calls.append(tool_call)
#                 response.tool_calls = unique_tool_calls

#             return {
#                 "messages": state["messages"] + [response],
#                 "next": "tools"
#                 if hasattr(response, "tool_calls") and response.tool_calls
#                 else "supervisor",
#                 "tool_output": state.get("tool_output", ToolOutput()),
#             }

#         # --- 3. Define Worker Node 2 (Mapping Tasks) - MODIFIED ---
#         def call_worker_node_2(state: WorkflowState):
#             print("---WORKER NODE 2 (MAPPING AGENT)---")
#             # CHANGE START: Escaped curly braces and moved partial to invoke
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         "You are a data mapping specialist. A previous tool call has unzipped files. Your task is to use the 'map_csvs_to_ingestion_args_tool' with the unzipped file paths from the tool output to map the data to ingestion arguments. The unzipped file paths are available in the 'result' attribute of the tool output from the state: {tool_output_result}. "
#                         "Ensure your tool call uses 'file_paths' as the argument name, like so: 'map_csvs_to_ingestion_args_tool(file_paths={{...}})'.",
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             )
#             llm_with_tools = self.llm.bind_tools(self.worker_2_tools)
#             chain = prompt | llm_with_tools
#             response = chain.invoke(
#                 {
#                     "messages": state["messages"],
#                     "tool_output_result": str(
#                         state.get("tool_output", ToolOutput()).result
#                     ),
#                 }
#             )
#             # CHANGE END
#             if hasattr(response, "tool_calls") and response.tool_calls:
#                 seen = set()
#                 unique_tool_calls = []
#                 for tool_call in response.tool_calls:
#                     tool_key = (tool_call["name"], str(tool_call["args"]))
#                     if tool_key not in seen:
#                         seen.add(tool_key)
#                         unique_tool_calls.append(tool_call)
#                 response.tool_calls = unique_tool_calls

#             print(f"\n\ntool_output: {state.get('tool_output', ToolOutput())}")
#             return {
#                 "messages": state["messages"] + [response],
#                 "next": "tools"
#                 if hasattr(response, "tool_calls") and response.tool_calls
#                 else "supervisor",
#                 "tool_output": state.get("tool_output", ToolOutput()),
#             }

#         # --- 4. Define Worker Node 3 (Inserting Task)
#         def call_worker_node_3(state: WorkflowState):
#             print("---WORKER NODE 3 (INSERTING AGENT)---")
#             # CHANGE START: Escaped curly braces and moved partial to invoke
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         "You are a data insertion specialist. Use the 'insert_ingestion_args_into_database_tool' with a dictionary of lists of ingestion arguments from the previous tool output. The dictionary is in the 'result' attribute of the tool output from the state: {tool_output_result}. "
#                         "Ensure your tool call uses 'ingestion_args_dict' as the argument name, like so: 'insert_ingestion_args_into_database_tool(ingestion_args_dict={{...}})'.",
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             )
#             llm_with_tools = self.llm.bind_tools(self.worker_3_tools)
#             chain = prompt | llm_with_tools
#             response = chain.invoke(
#                 {
#                     "messages": state["messages"],
#                     "tool_output_result": str(
#                         state.get("tool_output", ToolOutput()).result
#                     ),
#                 }
#             )
#             # CHANGE END
#             if hasattr(response, "tool_calls") and response.tool_calls:
#                 seen = set()
#                 unique_tool_calls = []
#                 for tool_call in response.tool_calls:
#                     tool_key = (tool_call["name"], str(tool_call["args"]))
#                     if tool_key not in seen:
#                         seen.add(tool_key)
#                         unique_tool_calls.append(tool_call)
#                 response.tool_calls = unique_tool_calls

#             print(f"\n\ntool_output: {state.get('tool_output', ToolOutput())}")
#             return {
#                 "messages": state["messages"] + [response],
#                 "next": "tools"
#                 if hasattr(response, "tool_calls") and response.tool_calls
#                 else "supervisor",
#                 "tool_output": state.get(
#                     "tool_output", ToolOutput()
#                 ),  # Preserve tool output
#             }

#         # def _parse_tool_output_string(output_string: str) -> dict:
#         #     """
#         #     Parses a custom tool output string of the format 'message="..." result=[...]'
#         #     and returns a dictionary. Used as fallback for string outputs.
#         #     """
#         #     parsed_dict = {}
#         #     message_match = re.search(r"message='(.*?)'", output_string, re.DOTALL)
#         #     if message_match:
#         #         parsed_dict["message"] = message_match.group(1)

#         #     result_match = re.search(
#         #         r"result=({.*?}|\[.*?\]|None)", output_string, re.DOTALL
#         #     )
#         #     if result_match:
#         #         try:
#         #             parsed_dict["result"] = ast.literal_eval(result_match.group(1))
#         #         except (ValueError, SyntaxError) as e:
#         #             logger.error(f"Error parsing result literal from string: {e}")
#         #             parsed_dict["result"] = None

#         #     return parsed_dict

#         # async def tool_executor_node(state: WorkflowState):
#         #     print("---TOOL EXECUTOR---")
#         #     last_message = state["messages"][-1]
#         #     tool_messages_to_add = []

#         #     # Default tool_output
#         #     tool_output = state.get(
#         #         "tool_output", ToolOutput(message="No tool call executed.", result=None)
#         #     )

#         #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#         #         for tool_call in last_message.tool_calls:
#         #             tool_name = tool_call["name"]
#         #             tool_args = tool_call["args"]
#         #             tool = next(
#         #                 (t for t in self.all_tools if t.name == tool_name), None
#         #             )
#         #             if not tool:
#         #                 logger.error(f"Tool {tool_name} not found")
#         #                 tool_messages_to_add.append(
#         #                     ToolMessage(
#         #                         content=f"Error: Tool {tool_name} not found",
#         #                         tool_call_id=tool_call["id"],
#         #                     )
#         #                 )
#         #                 continue
#         #             try:
#         #                 result = await tool._arun(**tool_args)
#         #                 if isinstance(result, ToolOutput):
#         #                     tool_output = result
#         #                 elif isinstance(result, dict):
#         #                     tool_output = ToolOutput(
#         #                         message=result.get("message", "Message not provided."),
#         #                         result=result.get("result", None),
#         #                     )
#         #                 else:
#         #                     parsed_dict = _parse_tool_output_string(str(result))
#         #                     tool_output = ToolOutput(
#         #                         message=parsed_dict.get(
#         #                             "message", "Could not parse string output."
#         #                         ),
#         #                         result=parsed_dict.get("result", None),
#         #                     )
#         #                 tool_messages_to_add.append(
#         #                     ToolMessage(
#         #                         content=str(
#         #                             tool_output
#         #                         ),  # Serialize for message history
#         #                         tool_call_id=tool_call["id"],
#         #                     )
#         #                 )
#         #             except Exception as e:
#         #                 logger.error(f"Error executing tool {tool_name}: {e}")
#         #                 tool_output = ToolOutput(
#         #                     message=f"Error executing tool {tool_name}: {str(e)}",
#         #                     result=None,
#         #                 )
#         #                 tool_messages_to_add.append(
#         #                     ToolMessage(
#         #                         content=str(tool_output), tool_call_id=tool_call["id"]
#         #                     )
#         #                 )

#         #     print(f" --> tool_output: {tool_output}")
#         #     return {
#         #         "messages": state["messages"] + tool_messages_to_add,
#         #         "tool_output": tool_output,
#         #     }

#         # async def tool_executor_node(state: dict[str, Any]) -> dict[str, Any]:
#         #     # ... (code before the try block) ...

#         #     try:
#         #         tool_outputs = await tool_executor.ainvoke({"messages": [last_message]})
#         #         print(f" ******** tool_outputs: {tool_outputs}")

#         #         # Check if there are messages to process
#         #         if not tool_outputs["messages"]:
#         #             tool_output = ToolOutput(
#         #                 message="No output received from tool executor."
#         #             )
#         #         else:
#         #             first_tool_message = tool_outputs["messages"][0]
#         #             print(f" ******** first_tool_message: {first_tool_message}")

#         #             if isinstance(first_tool_message, ToolMessage):
#         #                 # Handle both success and error cases from the tool
#         #                 if first_tool_message.status == "error":
#         #                     tool_output = ToolOutput(
#         #                         message=f"Tool execution failed: {first_tool_message.content}",
#         #                         result=None,
#         #                     )
#         #                 else:
#         #                     # Parse the content string manually
#         #                     try:
#         #                         # Use a regular expression to find the 'message' and 'result' parts
#         #                         match = re.match(
#         #                             r"message='(.*?)' result=(.*)",
#         #                             first_tool_message.content,
#         #                         )
#         #                         if match:
#         #                             message_part = match.group(1)
#         #                             result_part = match.group(2)

#         #                             # Safely evaluate the result part, which should be a list or dict
#         #                             parsed_result = ast.literal_eval(result_part)

#         #                             tool_output = ToolOutput(
#         #                                 message=message_part,
#         #                                 result=parsed_result,
#         #                             )
#         #                         else:
#         #                             # Fallback if the regex doesn't match the expected format
#         #                             tool_output = ToolOutput(
#         #                                 message=first_tool_message.content
#         #                             )
#         #                     except (ValueError, SyntaxError) as e:
#         #                         print(f"Error parsing tool output: {e}")
#         #                         # Fallback if ast.literal_eval fails
#         #                         tool_output = ToolOutput(
#         #                             message=first_tool_message.content
#         #                         )
#         #             else:
#         #                 # If the message is not a ToolMessage, just use its content.
#         #                 tool_output = ToolOutput(
#         #                     message=str(first_tool_message.content)
#         #                 )

#         #     except Exception as e:
#         #         logger.error(f"Error executing tool: {e}")
#         #         tool_output = ToolOutput(message=f"Error executing tool: {str(e)}")

#         #     print(f" --> tool_output: {tool_output}")
#         #     return {
#         #         "messages": state["messages"] + tool_outputs["messages"],
#         #         "tool_output": tool_output,
#         #     }

#         # async def tool_executor_node(state: dict[str, Any]) -> dict[str, Any]:
#         #     """Execute tools using ToolNode and return updated state with ToolOutput."""
#         #     print("---TOOL EXECUTOR---")
#         #     tool_executor = ToolNode(self.all_tools)
#         #     last_message = state["messages"][-1]
#         #     tool_output = state.get(
#         #         "tool_output", ToolOutput(message="No tool call executed.")
#         #     )

#         #     if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
#         #         print(f" --> tool_output: {tool_output}")
#         #         return {"messages": state["messages"], "tool_output": tool_output}

#         #     try:
#         #         tool_outputs = await tool_executor.ainvoke({"messages": [last_message]})
#         #         print(f" ******** tool_outputs: {tool_outputs}")
#         #         # Extract the first tool output (assuming single tool call for simplicity)
#         #         raw_output = (
#         #             tool_outputs["messages"][0].content
#         #             if tool_outputs["messages"]
#         #             else "No output received."
#         #         )

#         #         # Convert to ToolOutput
#         #         if isinstance(raw_output, ToolOutput):
#         #             tool_output = raw_output
#         #         elif isinstance(raw_output, dict):
#         #             tool_output = ToolOutput(
#         #                 message=raw_output.get("message", "Message not provided."),
#         #                 result=raw_output.get("result"),
#         #             )
#         #         else:
#         #             tool_output = ToolOutput(message=str(raw_output))

#         #     except Exception as e:
#         #         logger.error(f"Error executing tool: {e}")
#         #         tool_output = ToolOutput(message=f"Error executing tool: {str(e)}")

#         #     print(f" --> tool_output: {tool_output}")
#         #     return {
#         #         "messages": state["messages"] + tool_outputs["messages"],
#         #         "tool_output": tool_output,
#         #     }

#         async def tool_executor_node(state: WorkflowState):
#             print("---TOOL EXECUTOR---")
#             last_message = state["messages"][-1]
#             tool_messages_to_add = []

#             # Default tool_output
#             tool_output = state.get(
#                 "tool_output", ToolOutput(message="No tool call executed.", result=None)
#             )

#             if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#                 for tool_call in last_message.tool_calls:
#                     tool_name = tool_call["name"]
#                     tool_args = tool_call["args"]
#                     tool = next(
#                         (t for t in self.all_tools if t.name == tool_name), None
#                     )
#                     if not tool:
#                         logger.error(f"Tool {tool_name} not found")
#                         tool_messages_to_add.append(
#                             ToolMessage(
#                                 content=f"Error: Tool {tool_name} not found",
#                                 tool_call_id=tool_call["id"],
#                             )
#                         )
#                         continue
#                     try:
#                         result = await tool._arun(**tool_args)
#                         if isinstance(result, ToolOutput):
#                             tool_output = result

#                         if isinstance(result, dict):
#                             tool_output = ToolOutput(
#                                 message=result.get("message", "Message not provided."),
#                                 result=result.get("result", None),
#                             )

#                         tool_messages_to_add.append(
#                             ToolMessage(
#                                 content=str(
#                                     tool_output
#                                 ),  # Serialize for message history
#                                 tool_call_id=tool_call["id"],
#                             )
#                         )
#                     except Exception as e:
#                         logger.error(f"Error executing tool {tool_name}: {e}")
#                         tool_output = ToolOutput(
#                             message=f"Error executing tool {tool_name}: {str(e)}",
#                             result=None,
#                         )
#                         tool_messages_to_add.append(
#                             ToolMessage(
#                                 content=str(tool_output), tool_call_id=tool_call["id"]
#                             )
#                         )

#             print(f" --> tool_output: {tool_output}")
#             return {
#                 "messages": state["messages"] + tool_messages_to_add,
#                 "tool_output": tool_output,
#             }

#         # 6. Build the Graph
#         workflow.add_node("supervisor", call_supervisor)
#         workflow.add_node("worker_node_1", call_worker_node_1)
#         workflow.add_node("worker_node_2", call_worker_node_2)
#         workflow.add_node("worker_node_3", call_worker_node_3)
#         workflow.add_node("tools", tool_executor_node)

#         workflow.set_entry_point("supervisor")

#         # The supervisor's routing logic is now expanded
#         workflow.add_conditional_edges(
#             "supervisor",
#             lambda state: state["next"],
#             {
#                 "worker_node_1": "worker_node_1",
#                 "worker_node_2": "worker_node_2",
#                 "worker_node_3": "worker_node_3",
#                 "FINISH": END,
#             },
#         )

#         # def call_tools(
#         #     state: WorkflowState,
#         #     routes_to: str,
#         # ) -> str:
#         #     last_message = state["messages"][-1]
#         #     logger.info(f"Last message: {last_message}")
#         #     return (
#         #         "tools"
#         #         if hasattr(last_message, "tool_calls") and last_message.tool_calls
#         #         else routes_to
#         #     )

#         # Edges from workers to the tool executor
#         workflow.add_edge("worker_node_1", "tools")
#         workflow.add_edge("worker_node_2", "tools")
#         workflow.add_edge("worker_node_3", "tools")
#         # workflow.add_conditional_edges(
#         #     "worker_node_1",
#         #     path=functools.partial(call_tools, routes_to="supervisor"),
#         #     path_map={
#         #         "tools": "tools",
#         #         "supervisor": "supervisor",
#         #     },
#         # )
#         # workflow.add_conditional_edges(
#         #     "worker_node_2",
#         #     path=functools.partial(call_tools, routes_to="supervisor"),
#         #     path_map={
#         #         "tools": "tools",
#         #         "supervisor": "supervisor",
#         #     },
#         # )
#         # workflow.add_conditional_edges(
#         #     "worker_node_3",
#         #     path=functools.partial(call_tools, routes_to="supervisor"),
#         #     path_map={
#         #         "tools": "tools",
#         #         "supervisor": "supervisor",
#         #     },
#         # )

#         # After any tool is executed, always loop back to the supervisor
#         workflow.add_edge("tools", "supervisor")

#         # Compile the graph
#         graph = workflow.compile(checkpointer=MemorySaver())
#         print("✅ Graph with all worker nodes compiled successfully!")
#         print(graph.get_graph(xray=True).draw_ascii())
#         return graph

#     @property
#     def graph(self):
#         return self.__graph

#     # The `run` method from the previous answer can be used here without changes.
#     async def run(self, input_message: str) -> dict:
#         print(f"🚀 Starting {self.__name} with input: '{input_message[:100]}...'")
#         input_messages = [HumanMessage(content=input_message)]
#         thread_id = str(uuid.uuid4())
#         input_state = {"messages": input_messages}
#         result = await self.__graph.ainvoke(
#             input_state,
#             config={"configurable": {"thread_id": thread_id}},
#         )
#         print("\n✅ DataIngestionWorkflow Finished.")
#         final_message = "Workflow complete."
#         for msg in reversed(result.get("messages", [])):
#             if isinstance(msg, AIMessage) and msg.content:
#                 final_message = msg.content
#                 break
#         print(f"Final Result: {final_message}")
#         return result


###########


# import os
# import re
# import uuid
# import zipfile
# from typing import Annotated, Any, Sequence, Type, TypedDict
# import pandas as pd
# from langchain_core.language_models import BaseChatModel
# from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.tools import BaseTool
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import END, StateGraph
# from langgraph.graph.message import add_messages
# from pydantic import BaseModel, ConfigDict, Field
# from sqlalchemy.exc import IntegrityError
# from src.layers.business_layer.ai_agents.models.invoice_item_model import (
#     InvoiceItemModel,
# )
# from src.layers.business_layer.ai_agents.models.invoice_model import InvoiceModel
# from src.layers.core_logic_layer.logging import logger
# from src.layers.data_access_layer.postgresdb.models.invoice_item_model import (
#     InvoiceItemModel as SQLAlchemyInvoiceItemModel,
# )
# from src.layers.data_access_layer.postgresdb.models.invoice_model import (
#     InvoiceModel as SQLAlchemyInvoiceModel,
# )
# from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB


# # --- Pydantic model definitions with the fix ---
# class InvoiceIngestionConfig(BaseModel):
#     table_name: str = Field(default="invoice", description="Database table name.")
#     model: InvoiceModel = Field(..., description="Pydantic InvoiceModel class.")


# class InvoiceItemIngestionConfig(BaseModel):
#     table_name: str = Field(default="invoice_item", description="Database table name.")
#     model: InvoiceItemModel = Field(..., description="Pydantic InvoiceItemModel class.")


# class ToolOutput(BaseModel):
#     message: str = ""
#     result: Any = None

#     model_config = ConfigDict(arbitrary_types_allowed=True)


# class WorkflowState(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], add_messages]
#     next: str
#     tool_output: ToolOutput


# class UnzipFilesFromZipArchiveInput(BaseModel):
#     """Input schema for UnzipFilesFromZipArchiveTool."""

#     file_path: str = Field(..., description="Path to the ZIP file.")
#     destination_dir_path: str = Field(
#         ..., description="Path to the destination directory."
#     )


# class UnzipFilesFromZipArchiveTool(BaseTool):
#     name: str = "unzip_files_from_zip_archive_tool"
#     description: str = """
#     Unzip files from ZIP archive to a destination directory.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (list of paths of extracted files from ZIP archive on success or empty list on failure).
#     """
#     args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

#     def _run(self, file_path: str, destination_dir_path: str) -> ToolOutput:
#         logger.info("The UnzipFilesFromZipArchiveTool call has started...")
#         try:
#             # Ensure the destination directory exists
#             os.makedirs(destination_dir_path, exist_ok=True)

#             # List to store extracted file paths
#             extracted_files = []

#             # Unzip the file
#             with zipfile.ZipFile(file_path, "r") as zip_ref:
#                 zip_ref.extractall(destination_dir_path)
#                 # Get the list of extracted files
#                 extracted_files = [
#                     os.path.join(destination_dir_path, name)
#                     for name in zip_ref.namelist()
#                     if not name.endswith("/")
#                 ]

#             # Normalize file paths to use forward slashes
#             extracted_files = [file.replace("\\", "/") for file in extracted_files]

#             message = f"Success: ZIP file {file_path} extracted"
#             logger.info(f"{message}: {','.join(extracted_files)}")
#             logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
#             return ToolOutput(message=message, result=extracted_files)

#         except Exception as e:
#             message = f"Error unzipping file {file_path}: {str(e)}"
#             logger.error(message)
#             logger.info("The UnzipFilesFromZipArchiveTool call has finished.")
#             return ToolOutput(message=message, result=[])

#     async def _arun(self, file_path: str, destination_dir_path: str) -> ToolOutput:
#         return self._run(file_path=file_path, destination_dir_path=destination_dir_path)


# class MapCSVsToIngestionArgsInput(BaseModel):
#     """Input schema for MapCSVsToIngestionArgsTool."""

#     file_paths: list[str] = Field(
#         ..., description="List of paths of extracted CSV files."
#     )


# class MapCSVsToIngestionArgsTool(BaseTool):
#     name: str = "map_csvs_to_ingestion_args_tool"
#     description: str = """
#     Map a list of paths of extracted CSV files to a dictionary of lists of ingestion arguments.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (dictionary with integer keys and lists of ingestion arguments on success or None on failure.)
#     """
#     args_schema: Type[BaseModel] = MapCSVsToIngestionArgsInput

#     def _run(self, file_paths: list[str]) -> ToolOutput:
#         logger.info("The MapCSVsToIngestionArgsTool call has started...")
#         suffix_to_args: dict[
#             tuple[int, str],
#             tuple[
#                 InvoiceIngestionConfig | InvoiceItemIngestionConfig,
#                 InvoiceModel | InvoiceItemModel,
#             ],
#         ] = {
#             (0, "NFe_NotaFiscal"): (InvoiceIngestionConfig, InvoiceModel),
#             (1, "NFe_NotaFiscalItem"): (InvoiceItemIngestionConfig, InvoiceItemModel),
#         }
#         ingestion_args_dict: dict[
#             int, list[InvoiceIngestionConfig | InvoiceItemIngestionConfig]
#         ] = dict()

#         for file_path in file_paths:
#             file_name = os.path.basename(file_path)
#             for (key, suffix), (args_class, model_class) in suffix_to_args.items():
#                 if ingestion_args_dict.get(key) is None:
#                     ingestion_args_dict[key] = []

#                 if re.match(rf"\d{{6}}_{suffix}\.csv$", file_name):
#                     try:
#                         df = pd.read_csv(
#                             file_path,
#                             encoding="latin1",
#                             sep=";",
#                             dtype=model_class.get_csv_columns_to_dtypes()
#                             if hasattr(model_class, "get_csv_columns_to_dtypes")
#                             else str,
#                         )
#                     except FileNotFoundError as error:
#                         message = f"Error: Failed to find file at {file_path}: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)
#                     except UnicodeDecodeError as error:
#                         message = f"Error: Failed to decode data from file {file_path}: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)
#                     except Exception as error:
#                         message = f"Error: Failed to read file {file_path}: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)

#                     try:
#                         for index, row in df.iterrows():
#                             try:
#                                 model_data = {}
#                                 for (
#                                     csv_col,
#                                     doc_field_info,
#                                 ) in model_class.get_csv_columns_to_model_fields().items():
#                                     field_name = doc_field_info["field"]
#                                     converter = doc_field_info.get("converter")
#                                     value = row.get(csv_col)
#                                     if value is pd.NA or pd.isna(value):
#                                         value = None

#                                     if converter:
#                                         try:
#                                             value = converter(value)
#                                         except ValueError as error:
#                                             message = f"Warning: Could not convert '{value}' for field '{field_name}' in row {index + 1} of {file_path}: {error}"
#                                             logger.warning(message)
#                                             continue
#                                     model_data[field_name] = value
#                                 model = model_class(**model_data)
#                                 ingestion_args_dict[key].append(args_class(model=model))
#                             except Exception as error:
#                                 message = f"Error: Failed to process row {index + 1} from {file_path}: {error}"
#                                 logger.error(message)
#                                 continue
#                         message = f"Success: Models mapped from file {file_path}"
#                     except Exception as error:
#                         message = f"Error: Failed to map ingestion arguments dict {ingestion_args_dict} to models dict: {error}"
#                         logger.error(message)
#                         return ToolOutput(message=message, result=None)

#         serialized_models_dict = {
#             key: [
#                 {
#                     "table_name": ingestion_arg.table_name,
#                     "model": ingestion_arg.model.model_dump(),
#                 }
#                 for ingestion_arg in ingestion_args
#             ]
#             for key, ingestion_args in ingestion_args_dict.items()
#         }

#         logger.info("The MapCSVsToPydanticModelsTool call has finished.")
#         return ToolOutput(message=message, result=serialized_models_dict)

#     async def _arun(self, file_paths: list[str]) -> ToolOutput:
#         return self._run(file_paths=file_paths)


# class InsertIngestionArgsIntoDatabaseInput(BaseModel):
#     """Input schema for InsertIngestionArgsIntoDatabaseTool."""

#     ingestion_args_dict: dict[
#         int, list[InvoiceIngestionConfig | InvoiceItemIngestionConfig]
#     ] = Field(..., description="A dictionary of lists of ingestion arguments.")


# class InsertIngestionArgsIntoDatabaseTool(BaseTool):
#     name: str = "insert_ingestion_args_into_database_tool"
#     description: str = """
#     Insert SQLAlchemy database models into Postgres database.
#     Returns:
#         ToolOutput: An object containing a status message indicating success, warning or failure
#         (string) and result (total number of inserted records on success or None on failure).
#     """
#     postgresdb: PostgresDB
#     args_schema: Type[BaseModel] = InsertIngestionArgsIntoDatabaseInput

#     def __init__(self, postgresdb: PostgresDB):
#         super().__init__(postgresdb=postgresdb)
#         self.postgresdb = postgresdb

#     async def _arun(
#         self,
#         ingestion_args_dict: dict[int, list[dict[str, Any]]],
#     ) -> ToolOutput:
#         logger.info("The InsertIngestionArgsIntoDatabaseTool call has started...")
#         sqlalchemy_models_dict: dict[
#             int, list[SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel]
#         ] = dict()

#         for key, ingestion_args_list in ingestion_args_dict.items():
#             if sqlalchemy_models_dict.get(key) is None:
#                 sqlalchemy_models_dict[key] = []

#             for ingestion_args in ingestion_args_list:
#                 table_name = ingestion_args["table_name"]
#                 model_class: Type[SQLAlchemyInvoiceModel | SQLAlchemyInvoiceItemModel]
#                 # Replace match with if-elif
#                 if table_name == SQLAlchemyInvoiceModel.get_table_name():
#                     model_class = SQLAlchemyInvoiceModel
#                 elif table_name == SQLAlchemyInvoiceItemModel.get_table_name():
#                     model_class = SQLAlchemyInvoiceItemModel
#                 else:
#                     message = f"Error: Invalid table name {table_name}"
#                     logger.error(message)
#                     return ToolOutput(message=message, result=None)

#                 try:
#                     model = model_class.from_data(data=ingestion_args["model"])
#                     sqlalchemy_models_dict[key].append(model)
#                 except Exception as error:
#                     message = f"Error: Failed to create SQLAlchemy model from args {ingestion_args}: {error}"
#                     logger.error(message)
#                     continue

#         count_map: dict[str, int] = dict()
#         try:
#             async with self.postgresdb.async_session() as async_session:
#                 if len(sqlalchemy_models_dict) > 0:
#                     for _, models in sorted(sqlalchemy_models_dict.items()):
#                         for model in models:
#                             if count_map.get(model.get_table_name(), None) is None:
#                                 count_map[model.get_table_name()] = 0
#                             try:
#                                 async_session.add(model)
#                                 count_map[model.get_table_name()] += 1
#                             except IntegrityError:
#                                 message = f"Warning: Model already exists. Skipping duplicate model: {getattr(model, 'access_key', 'N/A')}"
#                                 logger.warning(message)
#                                 continue
#                             except Exception as error:
#                                 await async_session.rollback()
#                                 message = (
#                                     f"Error: Failed to insert model {model}: {error}"
#                                 )
#                                 logger.error(message)
#                                 return ToolOutput(message=message, result=None)
#                         try:
#                             await async_session.commit()
#                             message = f"Success: All {model.get_table_name()} table records have been committed."
#                             logger.info(message)
#                         except Exception as error:
#                             await async_session.rollback()
#                             message = f"Error: Failed to commit the current transaction: {error}"
#                             logger.error(message)
#                             return ToolOutput(message=message, result=None)
#         except Exception as error:
#             message = f"Error: Failed to establish database connection: {error}"
#             logger.error(message)
#             return ToolOutput(message=message, result=None)

#         if len(count_map) > 0:
#             total_count: int = 0
#             for model_name, count in count_map.items():
#                 total_count += count
#                 message = f"Success: {count} record(s) inserted into {model_name} table"
#                 logger.info(message)
#             message = f"Success: Total of {total_count} record(s) inserted into Postgres database"
#             logger.info("The InsertIngestionArgsIntoDatabaseTool call has finished.")
#             return ToolOutput(message=message, result=total_count)
#         else:
#             message = "Warning: No records to insert into Postgres database."
#             logger.warning(message)
#             return ToolOutput(message=message, result=0)

#     def _run(
#         self,
#         ingestion_args_dict: dict[int, list[dict]],
#     ) -> ToolOutput:
#         message = "Warning: Synchronous execution is not supported. Use _arun instead."
#         logger.warning(message)
#         raise NotImplementedError(message)


# class DataIngestionWorkflow:
#     def __init__(
#         self,
#         llm: BaseChatModel,
#         unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
#         map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
#         insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
#     ):
#         self.__name = "data_ingestion_workflow"
#         self.llm = llm

#         self.unzip_tool = unzip_files_from_zip_archive_tool
#         self.map_csvs_tool = map_csvs_to_ingestion_args_tool
#         self.insert_database_tool = insert_ingestion_args_into_database_tool
#         self.worker_1_tools = [self.unzip_tool]
#         self.worker_2_tools = [self.map_csvs_tool]
#         self.worker_3_tools = [self.insert_database_tool]
#         self.all_tools = self.worker_1_tools + self.worker_2_tools + self.worker_3_tools

#         self.__graph = self._build_graph()

#     def _build_graph(self) -> StateGraph:
#         workflow = StateGraph(state_schema=WorkflowState)

#         # --- 1. Define the Supervisor Node (Router) - UNCHANGED ---
#         def call_supervisor(state: WorkflowState):
#             print("---SUPERVISOR---")
#             messages = state["messages"]
#             worker_names = ["worker_node_1", "worker_node_2", "worker_node_3"]
#             worker_names_str = ", ".join(worker_names)
#             finish_node = '{{"next": "FINISH"}}'
#             entry_node = (
#                 f'{{{{"next": "{worker_names[0]}"}}}}'
#                 if worker_names
#                 else '{{"next": "FINISH"}}'
#             )
#             next_node = '{{"next": "<next_node>"}}'
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         """You are a supervisor routing tasks to workers. Based on the conversation history, decide the next step.
#                         Current available workers: [{worker_names_str}].
#                         Analyze the user request and conversation history to determine
#                         which worker can handle it best.

#                         If the input messages indicate that the task is complete, or if
#                         the state contains 'next': 'FINISH', return {finish_node}.

#                         Respond in the following JSON format:
#                         ```json
#                         {next_node}
#                         ```
#                         where <next_node> is the node to route to (e.g., {entry_node}
#                         or {finish_node}).
#                         """.format(
#                             worker_names_str=worker_names_str,
#                             finish_node=finish_node,
#                             next_node=next_node,
#                             entry_node=entry_node,
#                         ),
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             ).partial(
#                 worker_names_str=", ".join(worker_names_str),
#                 finish_node=finish_node,
#                 next_node=next_node,
#                 entry_node=entry_node,
#             )
#             chain = prompt | self.llm | JsonOutputParser()
#             response = chain.invoke({"messages": messages})
#             print(f"Supervisor routing to: {response['next']}")
#             return {"messages": messages, "next": response["next"]}

#         # --- 2. Define Worker Node 1 (Unzip Task) - UNCHANGED ---
#         def call_worker_node_1(state: WorkflowState):
#             print("---WORKER NODE 1 (UNZIP AGENT)---")
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         "You are an unzip specialist. You have access to a tool to unzip files. Call this tool to start the workflow.",
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             )
#             llm_with_tools = self.llm.bind_tools(self.worker_1_tools)
#             chain = prompt | llm_with_tools
#             response = chain.invoke({"messages": state["messages"]})
#             if hasattr(response, "tool_calls") and response.tool_calls:
#                 seen = set()
#                 unique_tool_calls = []
#                 for tool_call in response.tool_calls:
#                     tool_key = (tool_call["name"], str(tool_call["args"]))
#                     if tool_key not in seen:
#                         seen.add(tool_key)
#                         unique_tool_calls.append(tool_call)
#                 response.tool_calls = unique_tool_calls

#             return {
#                 "messages": state["messages"] + [response],
#                 "next": "tools"
#                 if hasattr(response, "tool_calls") and response.tool_calls
#                 else "supervisor",
#                 "tool_output": state.get("tool_output", ToolOutput()),
#             }

#         # --- 3. Define Worker Node 2 (Mapping Tasks) - MODIFIED ---
#         def call_worker_node_2(state: WorkflowState):
#             print("---WORKER NODE 2 (MAPPING AGENT)---")
#             # CHANGE START: Escaped curly braces and moved partial to invoke
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         "You are a data mapping specialist. A previous tool call has unzipped files. Your task is to use the 'map_csvs_to_ingestion_args_tool' with the unzipped file paths from the tool output to map the data to ingestion arguments. The unzipped file paths are available in the 'result' attribute of the tool output from the state: {tool_output_result}. "
#                         "Ensure your tool call uses 'file_paths' as the argument name, like so: 'map_csvs_to_ingestion_args_tool(file_paths={{...}})'.",
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             )
#             llm_with_tools = self.llm.bind_tools(self.worker_2_tools)
#             chain = prompt | llm_with_tools
#             response = chain.invoke(
#                 {
#                     "messages": state["messages"],
#                     "tool_output_result": str(
#                         state.get("tool_output", ToolOutput()).result
#                     ),
#                 }
#             )
#             # CHANGE END
#             if hasattr(response, "tool_calls") and response.tool_calls:
#                 seen = set()
#                 unique_tool_calls = []
#                 for tool_call in response.tool_calls:
#                     tool_key = (tool_call["name"], str(tool_call["args"]))
#                     if tool_key not in seen:
#                         seen.add(tool_key)
#                         unique_tool_calls.append(tool_call)
#                 response.tool_calls = unique_tool_calls

#             print(f"\n\ntool_output: {state.get('tool_output', ToolOutput())}")
#             return {
#                 "messages": state["messages"] + [response],
#                 "next": "tools"
#                 if hasattr(response, "tool_calls") and response.tool_calls
#                 else "supervisor",
#                 "tool_output": state.get("tool_output", ToolOutput()),
#             }

#         # --- 4. Define Worker Node 3 (Inserting Task)
#         def call_worker_node_3(state: WorkflowState):
#             print("---WORKER NODE 3 (INSERTING AGENT)---")
#             # CHANGE START: Escaped curly braces and moved partial to invoke
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         "You are a data insertion specialist. Use the 'insert_ingestion_args_into_database_tool' with a dictionary of lists of ingestion arguments from the previous tool output. The dictionary is in the 'result' attribute of the tool output from the state: {tool_output_result}. "
#                         "Ensure your tool call uses 'ingestion_args_dict' as the argument name, like so: 'insert_ingestion_args_into_database_tool(ingestion_args_dict={{...}})'.",
#                     ),
#                     MessagesPlaceholder(variable_name="messages"),
#                 ]
#             )
#             llm_with_tools = self.llm.bind_tools(self.worker_3_tools)
#             chain = prompt | llm_with_tools
#             response = chain.invoke(
#                 {
#                     "messages": state["messages"],
#                     "tool_output_result": str(
#                         state.get("tool_output", ToolOutput()).result
#                     ),
#                 }
#             )
#             # CHANGE END
#             if hasattr(response, "tool_calls") and response.tool_calls:
#                 seen = set()
#                 unique_tool_calls = []
#                 for tool_call in response.tool_calls:
#                     tool_key = (tool_call["name"], str(tool_call["args"]))
#                     if tool_key not in seen:
#                         seen.add(tool_key)
#                         unique_tool_calls.append(tool_call)
#                 response.tool_calls = unique_tool_calls

#             print(f"\n\ntool_output: {state.get('tool_output', ToolOutput())}")
#             return {
#                 "messages": state["messages"] + [response],
#                 "next": "tools"
#                 if hasattr(response, "tool_calls") and response.tool_calls
#                 else "supervisor",
#                 "tool_output": state.get(
#                     "tool_output", ToolOutput()
#                 ),  # Preserve tool output
#             }

#         # def _parse_tool_output_string(output_string: str) -> dict:
#         #     """
#         #     Parses a custom tool output string of the format 'message="..." result=[...]'
#         #     and returns a dictionary. Used as fallback for string outputs.
#         #     """
#         #     parsed_dict = {}
#         #     message_match = re.search(r"message='(.*?)'", output_string, re.DOTALL)
#         #     if message_match:
#         #         parsed_dict["message"] = message_match.group(1)

#         #     result_match = re.search(
#         #         r"result=({.*?}|\[.*?\]|None)", output_string, re.DOTALL
#         #     )
#         #     if result_match:
#         #         try:
#         #             parsed_dict["result"] = ast.literal_eval(result_match.group(1))
#         #         except (ValueError, SyntaxError) as e:
#         #             logger.error(f"Error parsing result literal from string: {e}")
#         #             parsed_dict["result"] = None

#         #     return parsed_dict

#         # async def tool_executor_node(state: WorkflowState):
#         #     print("---TOOL EXECUTOR---")
#         #     tool_executor = ToolNode(self.all_tools)
#         #     last_message = state["messages"][-1]
#         #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#         #         tool_outputs = await tool_executor.ainvoke({"messages": [last_message]})
#         #         # Extract the tool output (assuming single tool call for simplicity)
#         #         tool_output = (
#         #             tool_outputs["messages"][0].content
#         #             if tool_outputs["messages"]
#         #             else {}
#         #         )
#         #         print(f" --> tool_output: {tool_output}")
#         #         return {
#         #             "messages": state["messages"] + tool_outputs["messages"],
#         #             "tool_output": tool_output
#         #         }
#         #     return state

#         async def tool_executor_node(state: WorkflowState):
#             print("---TOOL EXECUTOR---")
#             last_message = state["messages"][-1]
#             tool_messages_to_add = []

#             # Default tool_output
#             tool_output = state.get(
#                 "tool_output", ToolOutput(message="No tool call executed.", result=None)
#             )

#             if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#                 for tool_call in last_message.tool_calls:
#                     tool_name = tool_call["name"]
#                     tool_args = tool_call["args"]
#                     tool = next(
#                         (t for t in self.all_tools if t.name == tool_name), None
#                     )
#                     if not tool:
#                         logger.error(f"Tool {tool_name} not found")
#                         tool_messages_to_add.append(
#                             ToolMessage(
#                                 content=f"Error: Tool {tool_name} not found",
#                                 tool_call_id=tool_call["id"],
#                             )
#                         )
#                         continue
#                     try:
#                         result = await tool._arun(**tool_args)
#                         if isinstance(result, ToolOutput):
#                             tool_output = result

#                         if isinstance(result, dict):
#                             tool_output = ToolOutput(
#                                 message=result.get("message", "Message not provided."),
#                                 result=result.get("result", None),
#                             )

#                         tool_messages_to_add.append(
#                             ToolMessage(
#                                 content=str(
#                                     tool_output
#                                 ),  # Serialize for message history
#                                 tool_call_id=tool_call["id"],
#                             )
#                         )
#                     except Exception as e:
#                         logger.error(f"Error executing tool {tool_name}: {e}")
#                         tool_output = ToolOutput(
#                             message=f"Error executing tool {tool_name}: {str(e)}",
#                             result=None,
#                         )
#                         tool_messages_to_add.append(
#                             ToolMessage(
#                                 content=str(tool_output), tool_call_id=tool_call["id"]
#                             )
#                         )

#             print(f" --> tool_output: {tool_output}")
#             return {
#                 "messages": state["messages"] + tool_messages_to_add,
#                 "tool_output": tool_output,
#             }

#         # async def tool_executor_node(state: dict[str, Any]) -> dict[str, Any]:
#         #     """Execute tools using ToolNode and return updated state with ToolOutput."""
#         #     print("---TOOL EXECUTOR---")
#         #     tool_executor = ToolNode(self.all_tools)
#         #     last_message = state["messages"][-1]
#         #     tool_output = state.get(
#         #         "tool_output", ToolOutput(message="No tool call executed.")
#         #     )

#         #     if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
#         #         print(f" --> tool_output: {tool_output}")
#         #         return {"messages": state["messages"], "tool_output": tool_output}

#         #     try:
#         #         tool_outputs = await tool_executor.ainvoke({"messages": [last_message]})
#         #         # Extract the first tool output (assuming single tool call for simplicity)
#         #         raw_output = (
#         #             tool_outputs["messages"][0].content
#         #             if tool_outputs["messages"]
#         #             else "No output received."
#         #         )

#         #         # Convert to ToolOutput
#         #         if isinstance(raw_output, ToolOutput):
#         #             tool_output = raw_output
#         #         elif isinstance(raw_output, dict):
#         #             tool_output = ToolOutput(
#         #                 message=raw_output.get("message", "Message not provided."),
#         #                 result=raw_output.get("result"),
#         #             )
#         #         else:
#         #             tool_output = ToolOutput(message=str(raw_output))

#         #     except Exception as e:
#         #         logger.error(f"Error executing tool: {e}")
#         #         tool_output = ToolOutput(message=f"Error executing tool: {str(e)}")

#         #     print(f" --> tool_output: {tool_output}")
#         #     return {
#         #         "messages": state["messages"] + tool_outputs["messages"],
#         #         "tool_output": tool_output,
#         #     }

#         # 6. Build the Graph
#         workflow.add_node("supervisor", call_supervisor)
#         workflow.add_node("worker_node_1", call_worker_node_1)
#         workflow.add_node("worker_node_2", call_worker_node_2)
#         workflow.add_node("worker_node_3", call_worker_node_3)
#         workflow.add_node("tools", tool_executor_node)

#         workflow.set_entry_point("supervisor")

#         # The supervisor's routing logic is now expanded
#         workflow.add_conditional_edges(
#             "supervisor",
#             lambda state: state["next"],
#             {
#                 "worker_node_1": "worker_node_1",
#                 "worker_node_2": "worker_node_2",
#                 "worker_node_3": "worker_node_3",
#                 "FINISH": END,
#             },
#         )

#         # def call_tools(
#         #     state: WorkflowState,
#         #     routes_to: str,
#         # ) -> str:
#         #     last_message = state["messages"][-1]
#         #     logger.info(f"Last message: {last_message}")
#         #     return (
#         #         "tools"
#         #         if hasattr(last_message, "tool_calls") and last_message.tool_calls
#         #         else routes_to
#         #     )

#         # Edges from workers to the tool executor
#         workflow.add_edge("worker_node_1", "tools")
#         workflow.add_edge("worker_node_2", "tools")
#         workflow.add_edge("worker_node_3", "tools")
#         # workflow.add_conditional_edges(
#         #     "worker_node_1",
#         #     path=functools.partial(call_tools, routes_to="supervisor"),
#         #     path_map={
#         #         "tools": "tools",
#         #         "supervisor": "supervisor",
#         #     },
#         # )
#         # workflow.add_conditional_edges(
#         #     "worker_node_2",
#         #     path=functools.partial(call_tools, routes_to="supervisor"),
#         #     path_map={
#         #         "tools": "tools",
#         #         "supervisor": "supervisor",
#         #     },
#         # )
#         # workflow.add_conditional_edges(
#         #     "worker_node_3",
#         #     path=functools.partial(call_tools, routes_to="supervisor"),
#         #     path_map={
#         #         "tools": "tools",
#         #         "supervisor": "supervisor",
#         #     },
#         # )

#         # After any tool is executed, always loop back to the supervisor
#         workflow.add_edge("tools", "supervisor")

#         # Compile the graph
#         graph = workflow.compile(checkpointer=MemorySaver())
#         print("✅ Graph with all worker nodes compiled successfully!")
#         print(graph.get_graph(xray=True).draw_ascii())
#         return graph

#     @property
#     def graph(self):
#         return self.__graph

#     # The `run` method from the previous answer can be used here without changes.
#     async def run(self, input_message: str) -> dict:
#         print(f"🚀 Starting {self.__name} with input: '{input_message[:100]}...'")
#         input_messages = [HumanMessage(content=input_message)]
#         thread_id = str(uuid.uuid4())
#         input_state = {"messages": input_messages}
#         result = await self.__graph.ainvoke(
#             input_state,
#             config={"configurable": {"thread_id": thread_id}},
#         )
#         print("\n✅ DataIngestionWorkflow Finished.")
#         final_message = "Workflow complete."
#         for msg in reversed(result.get("messages", [])):
#             if isinstance(msg, AIMessage) and msg.content:
#                 final_message = msg.content
#                 break
#         print(f"Final Result: {final_message}")
#         return result


###########

# def __call_supervisor(self, state: WorkflowState):
#         logger.info(f"Calling {self.supervisor_agent.name}...")
#         messages = state["messages"]

#         # if (
#         #     messages
#         #     and isinstance(messages[-1], AIMessage)
#         #     and messages[-1].content
#         # ):
#         #     # If the last message is a content-ful AIMessage (not a tool call),
#         #     # we assume this is the final answer and route to FINISH.
#         #     if not (
#         #         hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls
#         #     ):
#         #         logger.info("Supervisor found final answer. Routing to: FINISH")
#         #         return {"next": "FINISH"}

#         assistant_names = self.assistant_names
#         assistant_names_str = ", ".join(assistant_names)
#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     """
#                     You are a team supervisor routing tasks between the following assistants:
#                     {assistant_names_str}.
#                     - `assistant_1` is a specialist in unzipping files.
#                     - `assistant_2` is a specialist in reading the content of files.

#                     **Here are your CRITICAL instructions:**
#                     1. Your primary goal is to ensure the user's request is fully completed.
#                     2. Analyze the user request and the entire conversation history.
#                     3. Your task is to determine the NEXT step.

#                     **Routing Logic:**
#                     - If the **last message in the conversation** is a final, conclusive answer to the user's original request, route to FINISH.
#                     A final answer will be a human-readable message, not a tool-calling message or a tool output.
#                     - If the task requires a new action or a different assistant to proceed, route to the appropriate assistant.
#                     For example, if files have just been unzipped by `assistant_1`, and the user wants to know what's inside them, you should route to `assistant_2`.

#                     Respond with a JSON object with a single key 'next' mapping to one of [{assistant_names_str}, FINISH] as follows:
#                     ```json
#                         {{"next": "<next_node>"}}
#                     ```
#                     where <next_node> is the node to route to (e.g., {entry_node} or {finish_node}).
#                     """,
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         ).partial(
#             assistant_names_str=assistant_names_str,
#             finish_node="FINISH",
#             entry_node=self.assistant_names[0],
#         )
#         chain = prompt | self.llm | JsonOutputParser()
#         response = chain.invoke({"messages": messages})
#         logger.info(f"{self.supervisor.name} routing to: {response['next']}")
#         return {"next": response["next"]}

#     def __call_assistant_1(self, state: WorkflowState):
#         logger.info(f"Calling {self.assistant_1.name}...")
#         messages = state["messages"]
#         logger.info(f"messages: {messages}")
#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     """
#                     You are an unzip file specialist.
#                     - If asked to unzip a file, call the `UnzipFilesFromZipArchiveTool` immediately.
#                     - If you receive a `ToolMessage` with the result, summarize it to confirm the task is done."
#                     """,
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         )
#         llm_with_tools = self.llm.bind_tools(self.assistant_1.tools)
#         chain = prompt | llm_with_tools
#         response = chain.invoke({"messages": messages})

#         # The agent's response is the key to routing.
#         # We don't need to return 'next' here, the conditional edge will handle it.
#         # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
#         return {"messages": [response], "sender": self.assistant_1.name}

#     def __call_assistant_2(self, state: WorkflowState):
#         logger.info(f"Calling {self.assistant_2.name}...")
#         messages = state["messages"]
#         logger.info(f"messages: {messages}")
#         prompt = ChatPromptTemplate.from_messages(
#             [
#                 (
#                     "system",
#                     """
#                     You are a file reading specialist.
#                     - The user will ask you to read a file whose path was likely provided by `assistant_1`.
#                     - Look at the conversation history to find the file paths. Call the `ReadFileTool` to read the content of a file.
#                     - If you receive a `ToolMessage` from `ReadFileTool`, its output is an object with a 'result' field containing the file's content.
#                     - Your final answer should be a summary of this content. For example: "I have read the file. The content begins with: [first 100 characters of content]".
#                     """,
#                 ),
#                 MessagesPlaceholder(variable_name="messages"),
#             ]
#         )
#         llm_with_tools = self.llm.bind_tools(self.assistant_2.tools)
#         chain = prompt | llm_with_tools
#         response = chain.invoke({"messages": messages})

#         # The agent's response is the key to routing.
#         # We don't need to return 'next' here, the conditional edge will handle it.
#         # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
#         return {"messages": [response], "sender": self.assistant_2.name}

#     def __route_from_supervisor(self, state: WorkflowState):
#         logger.info(f"Routing from {self.supervisor.name}...")
#         next_node = state["next"]
#         logger.info(f"Routing decision: '{next_node}'")
#         return next_node

#     def __route_from_assistant(self, state: WorkflowState):
#         logger.info(f"Routing from {self.assistant_1.name}...")
#         last_message = state["messages"][-1]
#         logger.info(f"Last message content: {last_message.content}")
#         logger.info(
#             f"Tool calls found: {hasattr(last_message, 'tool_calls') and last_message.tool_calls}"
#         )

#         # If there are tool calls, go to the tools node.
#         if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#             logger.info("Routing decision: 'tools' (tool calls found)")
#             return "tools"
#         # If the LLM has provided a final answer, route back to the supervisor to finish.
#         elif hasattr(last_message, "content") and last_message.content:
#             logger.info(
#                 f"Routing decision: '{self.supervisor.name}' (final content found)"
#             )
#             return self.supervisor.name
#         # Otherwise, something went wrong, and we should probably route back to the supervisor
#         # or have a more robust error handling mechanism. For now, we'll route to supervisor.
#         else:
#             logger.warning(
#                 f"Routing decision: '{self.supervisor.name}' (no tool calls or final content)"
#             )
#             return self.supervisor.name

#     def __route_from_tools(self, state: WorkflowState):
#         logger.info("Routing from tools back to...")
#         next_node = state["sender"]
#         logger.info(f"Routing decision: '{next_node}'")
#         return next_node
