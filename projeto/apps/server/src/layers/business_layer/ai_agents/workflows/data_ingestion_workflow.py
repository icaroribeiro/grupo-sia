import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent

from src.layers.business_layer.ai_agents.models.data_ingestion_state_model import (
    DataIngestionStateModel,
)
from src.layers.business_layer.ai_agents.tools.data_ingestion_handoff_tool import (
    DataIngestionHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.insert_ingestion_args_into_database_tool import (
    InsertIngestionArgsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.logging import logger


class DataIngestionWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
    ):
        self.name = "data_ingestion_team"
        self.chat_model = chat_model
        self.file_unzipping_agent = create_react_agent(
            model=self.chat_model,
            tools=[unzip_files_from_zip_archive_tool],
            prompt=(
                """
                ROLE:
                - You're a file unzip agent.
                GOAL:
                - Your sole purpose is to unzip files. 
                - DO NOT perform any other tasks.
                """
            ),
            name="file_unzipping_agent",
        )
        self.csv_mapping_agent = create_react_agent(
            model=self.chat_model,
            tools=[map_csvs_to_ingestion_args_tool],
            prompt=(
                """
                ROLE:
                - You're a csv mapping agent.
                GOAL:
                - Your sole purpose is to map csv file. 
                - DO NOT perform any other tasks.
                INSTRUCTIONS:
                - Based on the conversation history, when using `map_csvs_to_ingestion_args_tool` tool the `csv_file_path` argument is the return of `unzip_files_from_zip_archive_tool` tool.
                - DO NOT create or invent file paths. Always use the paths from the previous step.
                """
            ),
            name="csv_mapping_agent",
        )
        self.ingestion_args_agent = create_react_agent(
            model=self.chat_model,
            tools=[insert_ingestion_args_into_database_tool],
            prompt=(
                """
                PROFILE:
                - You're an ingestion arguments agent.
                GOAL:
                - Your sole purpose is to insert ingestion arguments into database. 
                - DO NOT perform any other tasks.
                """
            ),
            name="ingestion_args_agent",
        )
        delegate_to_file_unzipping_agent = DataIngestionHandoffTool(
            agent_name=self.file_unzipping_agent.name,
        )
        delegate_to_csv_mapping_agent = DataIngestionHandoffTool(
            agent_name=self.csv_mapping_agent.name,
        )
        delegate_to_ingestion_args_agent = DataIngestionHandoffTool(
            agent_name=self.ingestion_args_agent.name
        )
        self.supervisor = create_react_agent(
            model=self.chat_model,
            tools=[
                delegate_to_file_unzipping_agent,
                delegate_to_csv_mapping_agent,
                delegate_to_ingestion_args_agent,
            ],
            prompt=(
                """
                ROLE:
                - You're a supervisor.
                GOAL:
                - Your sole purpose is to manage three agents:
                    - A File Unzipping Agent: Assign tasks related to unzipping files to this agent.
                    - A CSV Mapping Agent: Assign tasks related to mapping CSV files to this agent.
                    - An Ingestion Arguments Agent: Assign tasks related to inserting ingestion arguments to this agent.
                INSTRUCTIONS:
                - Based on the conversation history, decide the next step.
                - When request contains a file, folder or directory path, always inform it properly to the agent in the task description.
                - DO NOT create or invent file paths that where not informed in the request.
                - DO NOT do any work yourself.
                CRITICAL RULES:
                - ALWAYS assign work to one agent at a time.
                - DO NOT call agents in parallel.
                """
            ),
            name="supervisor",
        )
        self.__graph = self.__build_graph()

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=DataIngestionStateModel)

        builder.add_node(
            self.supervisor,
            destinations={
                self.file_unzipping_agent.name: self.file_unzipping_agent.name,
                self.csv_mapping_agent.name: self.csv_mapping_agent.name,
                self.ingestion_args_agent.name: self.ingestion_args_agent.name,
            },
        )
        builder.add_node(self.file_unzipping_agent)
        builder.add_node(self.csv_mapping_agent)
        builder.add_node(self.ingestion_args_agent)

        builder.add_edge(START, self.supervisor.name)
        builder.add_edge(self.file_unzipping_agent.name, self.supervisor.name)
        builder.add_edge(self.csv_mapping_agent.name, self.supervisor.name)
        builder.add_edge(self.ingestion_args_agent.name, self.supervisor.name)

        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        return graph

    async def run(self, input_message: str) -> MessagesState:
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
        return {"messages": result}

    # async def run(self, input_message: str) -> dict:
    #     logger.info(f"Starting {self.name} with input: '{input_message[:100]}...'")
    #     input_messages = [HumanMessage(content=input_message)]
    #     thread_id = str(uuid.uuid4())
    #     input_state = {"messages": input_messages}

    #     async for chunk in self.__graph.astream(
    #         input_state,
    #         subgraphs=True,
    #         config={"configurable": {"thread_id": thread_id}},
    #     ):
    #         self._pretty_print_messages(chunk, last_message=True)
    #     result = chunk[1]["supervisor"]["messages"]
    #     # for message in result:
    #     #     message.pretty_print()
    #     # result = await self.__graph.ainvoke(
    #     #     input_state,
    #     #     config={"configurable": {"thread_id": thread_id}},
    #     # )
    #     final_message = f"{self.name} complete."
    #     logger.info(f"{self.name} final result: {final_message}")
    #     return result
