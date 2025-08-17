import uuid
from src.layers.business_layer.ai_agents.tools.data_ingestion_handoff_tool import (
    DataIngestionHandoffTool,
)
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
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
from langgraph.prebuilt import create_react_agent


class DataIngestionWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
    ):
        self.name = "data_ingestion_workflow"
        self.chat_model = chat_model
        self.unzipping_agent = create_react_agent(
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
            name="unzipping_agent",
        )
        self.mapping_agent = create_react_agent(
            model=self.chat_model,
            tools=[map_csvs_to_ingestion_args_tool],
            prompt=(
                """
                ROLE:
                You're a csv mapping agent.
                GOAL:
                Your sole purpose is to map csv file. DO NOT perform any other tasks.
                INSTRUCTIONS:
                After you're done, respond to the supervisor with the ingestion arguments.
                CRITICAL RULES:
                Respond ONLY with the results of your work. DO NOT comment on other parts of the workflow.
                """
            ),
            name="mapping_agent",
        )
        self.inserting_agent = create_react_agent(
            model=self.chat_model,
            tools=[insert_ingestion_args_into_database_tool],
            prompt=(
                """
                PROFILE:
                You're an ingestion arguments inserter agent.
                GOAL:
                Your sole purpose is to insert ingestion arguments. DO NOT perform any other tasks.
                """
            ),
            name="inserting_agent",
        )
        delegate_to_unzipping_agent = DataIngestionHandoffTool(
            agent_name=self.unzipping_agent.name,
        )
        delegate_to_mapping_agent = DataIngestionHandoffTool(
            agent_name=self.mapping_agent.name,
        )
        delegate_to_inserting_agent = DataIngestionHandoffTool(
            agent_name=self.inserting_agent.name,
            insert_tool=insert_ingestion_args_into_database_tool,
        )
        self.supervisor = create_react_agent(
            model=self.chat_model,
            tools=[
                delegate_to_unzipping_agent,
                delegate_to_mapping_agent,
                delegate_to_inserting_agent,
            ],
            prompt=(
                """
                ROLE:
                You're a supervisor.
                GOAL:
                Your sole purpose is to manage three agents:
                A file unzipping agent. Assign unzip file-related tasks to this agent.
                A csv mapping agent. Assign map csv-related tasks to this agent.
                An ingestion arguments inserter agent. Assign insert ingestion-arguments-related tasks to this agent.
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
                self.unzipping_agent.name,
                self.mapping_agent.name,
                self.inserting_agent.name,
            ),
        )
        builder.add_node(self.unzipping_agent)
        builder.add_node(self.mapping_agent)
        builder.add_node(self.inserting_agent)
        builder.add_edge(START, self.supervisor.name)
        builder.add_edge(self.unzipping_agent.name, self.supervisor.name)
        builder.add_edge(self.mapping_agent.name, self.supervisor.name)
        builder.add_edge(self.inserting_agent.name, self.supervisor.name)
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
