import os
import uuid
import zipfile
from typing import Annotated, Any, Sequence, Type, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field
from langgraph.prebuilt import ToolNode

from src.layers.core_logic_layer.logging import logger


class ToolOutput(BaseModel):
    message: str = ""
    result: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str
    sender: str


class Agent(BaseModel):
    name: str
    tools: list[BaseTool] | None = None


class UnzipFilesFromZipArchiveInput(BaseModel):
    file_path: str = Field(..., description="Path to the ZIP file.")
    destination_dir_path: str = Field(
        ..., description="Path to the destination directory."
    )


class UnzipFilesFromZipArchiveTool(BaseTool):
    name: str = "unzip_files_from_zip_archive_tool"
    description: str = "Unzip files from ZIP archive to a destination directory."
    args_schema: Type[BaseModel] = UnzipFilesFromZipArchiveInput

    def _run(self, file_path: str, destination_dir_path: str) -> ToolOutput:
        logger.info(f"Running {self.name}...")
        try:
            os.makedirs(destination_dir_path, exist_ok=True)
            extracted_files = []
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(destination_dir_path)
                extracted_files = [
                    os.path.join(destination_dir_path, name)
                    for name in zip_ref.namelist()
                    if not name.endswith("/")
                ]
            extracted_files = [file.replace("\\", "/") for file in extracted_files]
            message = f"Success: ZIP file {file_path} extracted"
            logger.info(f"{message}: {','.join(extracted_files)}")
            tool_ouput = ToolOutput(message=message, result=extracted_files)
            logger.info(f"{self.name} result: {tool_ouput}")
            return ToolOutput(message=message, result=extracted_files)
        except Exception as error:
            message = f"Error unzipping file {file_path}: {str(error)}"
            logger.error(message)
            tool_ouput = ToolOutput(message=message, result=extracted_files)
            logger.info(f"{self.name} result: {tool_ouput}")
            return ToolOutput(message=message, result=[])

    async def _arun(self, file_path: str, destination_dir_path: str) -> ToolOutput:
        return self._run(file_path=file_path, destination_dir_path=destination_dir_path)


class ReadFileInput(BaseModel):
    file_path: str = Field(..., description="Path to the file to read.")


class ReadFileTool(BaseTool):
    name: str = "read_file_tool"
    description: str = "Reads the content of a single file."
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        logger.info(f"Running {self.name} on {file_path}...")
        try:
            with open(file_path, "r") as f:
                content = f.read()
            return f"Successfully read content from {file_path}: {content[:100]}..."
        except Exception as e:
            return f"Error reading file {file_path}: {e}"

    async def _arun(self, file_path: str) -> str:
        return self._run(file_path=file_path)


class DatabaseDataIngestionWorkflow:
    def __init__(
        self,
        llm: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        read_file_tool: ReadFileTool,
    ):
        self.name = "database_data_ingestion_workflow"
        self.llm = llm
        self.supervisor = Agent(name="supervisor")
        self.assistant_1 = Agent(
            name="assistant_1", tools=[unzip_files_from_zip_archive_tool]
        )
        self.assistant_2 = Agent(name="assistant_2", tools=[read_file_tool])
        self.assistant_names = [self.assistant_1.name, self.assistant_2.name]
        self.__graph = self._build_graph()

    def __call_supervisor(self, state: WorkflowState):
        logger.info(f"Calling {self.supervisor.name}...")
        messages = state["messages"]

        # if (
        #     messages
        #     and isinstance(messages[-1], AIMessage)
        #     and messages[-1].content
        # ):
        #     # If the last message is a content-ful AIMessage (not a tool call),
        #     # we assume this is the final answer and route to FINISH.
        #     if not (
        #         hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls
        #     ):
        #         logger.info("Supervisor found final answer. Routing to: FINISH")
        #         return {"next": "FINISH"}

        assistant_names = self.assistant_names
        assistant_names_str = ", ".join(assistant_names)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a team supervisor routing tasks between the following assistants: 
                    {assistant_names_str}.
                    - `assistant_1` is a specialist in unzipping files.
                    - `assistant_2` is a specialist in reading the content of files.
                    
                    **Here are your CRITICAL instructions:**
                    1. Your primary goal is to ensure the user's request is fully completed.
                    2. Analyze the user request and the entire conversation history.
                    3. Your task is to determine the NEXT step.
                    
                    **Routing Logic:**
                    - If the **last message in the conversation** is a final, conclusive answer to the user's original request, route to FINISH. 
                    A final answer will be a human-readable message, not a tool-calling message or a tool output.
                    - If the task requires a new action or a different assistant to proceed, route to the appropriate assistant.
                    For example, if files have just been unzipped by `assistant_1`, and the user wants to know what's inside them, you should route to `assistant_2`.
                                    
                    Respond with a JSON object with a single key 'next' mapping to one of [{assistant_names_str}, FINISH] as follows:
                    ```json
                        {{"next": "<next_node>"}}
                    ```
                    where <next_node> is the node to route to (e.g., {entry_node} or {finish_node}).
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            assistant_names_str=assistant_names_str,
            finish_node="FINISH",
            entry_node=self.assistant_names[0],
        )
        chain = prompt | self.llm | JsonOutputParser()
        response = chain.invoke({"messages": messages})
        logger.info(f"{self.supervisor.name} routing to: {response['next']}")
        return {"next": response["next"]}

    def __call_assistant_1(self, state: WorkflowState):
        logger.info(f"Calling {self.assistant_1.name}...")
        messages = state["messages"]
        logger.info(f"messages: {messages}")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are an unzip file specialist. 
                    - If asked to unzip a file, call the `UnzipFilesFromZipArchiveTool` immediately.
                    - If you receive a `ToolMessage` with the result, summarize it to confirm the task is done."
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        llm_with_tools = self.llm.bind_tools(self.assistant_1.tools)
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})

        # The agent's response is the key to routing.
        # We don't need to return 'next' here, the conditional edge will handle it.
        # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
        return {"messages": [response], "sender": self.assistant_1.name}

    def __call_assistant_2(self, state: WorkflowState):
        logger.info(f"Calling {self.assistant_2.name}...")
        messages = state["messages"]
        logger.info(f"messages: {messages}")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a file reading specialist. 
                    - The user will ask you to read a file whose path was likely provided by `assistant_1`.
                    - Look at the conversation history to find the file paths. Call the `ReadFileTool` to read the content of a file.
                    - If you receive a `ToolMessage` from `ReadFileTool`, its output is an object with a 'result' field containing the file's content.
                    - Your final answer should be a summary of this content. For example: "I have read the file. The content begins with: [first 100 characters of content]".
                    """,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        llm_with_tools = self.llm.bind_tools(self.assistant_2.tools)
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": messages})

        # The agent's response is the key to routing.
        # We don't need to return 'next' here, the conditional edge will handle it.
        # Return just the AIMessage response wrapped in a list. The `add_messages` will handle the append.
        return {"messages": [response], "sender": self.assistant_2.name}

    def __route_from_supervisor(self, state: WorkflowState):
        logger.info(f"Routing from {self.supervisor.name}...")
        next_node = state["next"]
        logger.info(f"Routing decision: '{next_node}'")
        return next_node

    def __route_from_assistant(self, state: WorkflowState):
        logger.info(f"Routing from {self.assistant_1.name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last message content: {last_message.content}")
        logger.info(
            f"Tool calls found: {hasattr(last_message, 'tool_calls') and last_message.tool_calls}"
        )

        # If there are tool calls, go to the tools node.
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("Routing decision: 'tools' (tool calls found)")
            return "tools"
        # If the LLM has provided a final answer, route back to the supervisor to finish.
        elif hasattr(last_message, "content") and last_message.content:
            logger.info(
                f"Routing decision: '{self.supervisor.name}' (final content found)"
            )
            return self.supervisor.name
        # Otherwise, something went wrong, and we should probably route back to the supervisor
        # or have a more robust error handling mechanism. For now, we'll route to supervisor.
        else:
            logger.warning(
                f"Routing decision: '{self.supervisor.name}' (no tool calls or final content)"
            )
            return self.supervisor.name

    def __route_from_tools(self, state: WorkflowState):
        logger.info("Routing from tools back to...")
        next_node = state["sender"]
        logger.info(f"Routing decision: '{next_node}'")
        return next_node

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(state_schema=WorkflowState)

        workflow.add_node(self.supervisor.name, self.__call_supervisor)
        workflow.add_node(self.assistant_1.name, self.__call_assistant_1)
        workflow.add_node(self.assistant_2.name, self.__call_assistant_2)
        workflow.add_node(
            node="tools",
            action=ToolNode(self.assistant_1.tools + self.assistant_2.tools),
        )

        workflow.set_entry_point(self.supervisor.name)

        routing_map = {name: name for name in self.assistant_names}
        routing_map["FINISH"] = END
        workflow.add_conditional_edges(
            self.supervisor.name,
            self.__route_from_supervisor,
            routing_map,
        )

        workflow.add_conditional_edges(
            self.assistant_1.name,
            self.__route_from_assistant,
            {"tools": "tools", self.supervisor.name: self.supervisor.name},
        )
        workflow.add_conditional_edges(
            self.assistant_2.name,
            self.__route_from_assistant,
            {"tools": "tools", self.supervisor.name: self.supervisor.name},
        )

        tool_routing_map = {name: name for name in self.assistant_names}
        workflow.add_conditional_edges(
            "tools", self.__route_from_tools, tool_routing_map
        )

        graph = workflow.compile(checkpointer=MemorySaver())
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(graph.get_graph(xray=True).draw_ascii())
        return graph

    @property
    def graph(self):
        return self.__graph

    async def run(self, input_message: str) -> dict:
        logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
        input_messages = [HumanMessage(content=input_message)]
        thread_id = str(uuid.uuid4())
        input_state = {"messages": input_messages}

        result = await self.__graph.ainvoke(
            input_state,
            config={"configurable": {"thread_id": thread_id}},
        )

        final_message = f"{self.name} complete."
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                final_message = msg.content
                break
        logger.info(f"{self.name} final result: {final_message}")
        return result
