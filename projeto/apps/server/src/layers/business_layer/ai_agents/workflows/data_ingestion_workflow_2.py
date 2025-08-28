import functools
import uuid
from src.layers.business_layer.ai_agents.models.shared_workflow_state_model import (
    SharedWorkflowStateModel,
)
from src.layers.business_layer.ai_agents.models.tool_output import ToolOutput
from src.layers.business_layer.ai_agents.tools.data_ingestion_handoff_tool import (
    DataIngestionHandoffTool,
)
from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage

from langgraph.prebuilt import create_react_agent
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import START, END
from langchain_core.language_models import BaseChatModel
from src.layers.business_layer.ai_agents.tools.insert_ingestion_args_into_database_tool import (
    InsertIngestionArgsIntoDatabaseTool,
)
from langgraph.prebuilt import ToolNode
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow


class DataIngestionWorkflow2(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
        map_csvs_to_ingestion_args_tool: MapCSVsToIngestionArgsTool,
        insert_ingestion_args_into_database_tool: InsertIngestionArgsIntoDatabaseTool,
    ):
        self.name = "data_ingestion_team"
        self.chat_model = chat_model

        self.unzip_files_from_zip_archive_tool = unzip_files_from_zip_archive_tool
        self.file_unzipping_agent = self.chat_model.bind_tools(
            [unzip_files_from_zip_archive_tool]
        )
        self.csv_mapping_agent = self.chat_model.bind_tools(
            [map_csvs_to_ingestion_args_tool]
        )
        self.ingestion_args_agent = self.chat_model.bind_tools(
            [insert_ingestion_args_into_database_tool]
        )
        delegate_to_file_unzipping_agent = DataIngestionHandoffTool(
            agent_name="file_unzipping_agent",
        )
        delegate_to_csv_mapping_agent = DataIngestionHandoffTool(
            agent_name="csv_mapping_agent",
        )
        delegate_to_ingestion_args_agent = DataIngestionHandoffTool(
            agent_name="ingestion_args_agent"
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
                - DO NOT do any work yourself.
                CRITICAL RULES:
                - ALWAYS assign work to one agent at a time.
                - DO NOT call agents in parallel.
                """
            ),
            name="supervisor",
        )
        self.all_tools = [
            unzip_files_from_zip_archive_tool,
            map_csvs_to_ingestion_args_tool,
            insert_ingestion_args_into_database_tool,
        ]
        self.__graph = self.__build_graph()

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=SharedWorkflowStateModel)

        def agent_node(
            state,
            name: str,
            prompt: str,
            llm_with_tools: Runnable[BaseMessage, BaseMessage],
        ):
            print(f"\nagent_node - name: {name}")
            print(f'\nagent_node - state["messages"]: {state["messages"]}')
            result = llm_with_tools.invoke(state["messages"])
            print(f"\nagent_node - result: {result}")
            return {"messages": state["messages"] + [result]}

        # Define a new function for the tools node
        def tools_node_with_output(state):
            # Access the most recent message, which should be a ToolMessage
            last_message = state["messages"][-1]

            # Check if the last message is a ToolMessage
            if not isinstance(last_message, ToolMessage):
                # If not, something is wrong with the graph flow.
                # You might want to handle this error case.
                logger.error("Expected ToolMessage but got a different type.")
                return {"messages": state["messages"]}

            # The ToolNode output is stored in the content of the ToolMessage
            tool_output_content = last_message.content

            # Now, use your custom parser to create the ToolOutput object
            parsed_tool_output = ToolOutput.from_tool_message(tool_output_content)
            logger.info(f"parsed_tool_output: {parsed_tool_output}")
            return {
                "messages": state["messages"],
                "tool_output": parsed_tool_output,
            }

        builder.add_node("supervisor", self.supervisor)
        builder.add_node(
            "file_unzipping_agent",
            functools.partial(
                agent_node,
                name="file_unzipping_agent",
                prompt=(
                    """
                ROLE:
                - You're a file unzip agent.
                GOAL:
                - Your sole purpose is to unzip files. 
                - DO NOT perform any other tasks.
                """
                ),
                llm_with_tools=self.file_unzipping_agent,
            ),
        )
        builder.add_node(
            "csv_mapping_agent",
            functools.partial(
                agent_node,
                name="csv_mapping_agent",
                prompt=(
                    """
                ROLE:
                - You're a csv mapping agent.
                GOAL:
                - Your sole purpose is to map csv file. 
                - DO NOT perform any other tasks.
                """
                ),
                llm_with_tools=self.csv_mapping_agent,
            ),
        )

        tool_chain = ToolNode(tools=self.all_tools) | tools_node_with_output
        builder.add_node("tools", tool_chain)

        def route_supervisor(state):
            last_message = state["messages"][-1]
            return (
                last_message.tool_calls[0].name
                if hasattr(last_message, "tool_calls") and last_message.tool_calls
                else END
            )

        def route_agent(state):
            last_message = state["messages"][-1]
            return (
                "tools"
                if hasattr(last_message, "tool_calls") and last_message.tool_calls
                else "supervisor"
            )

        builder.add_edge(START, "supervisor")
        builder.add_edge("tools", "supervisor")

        def return_state_node(state):
            return state

        # builder.add_node("return_state", return_state_node)

        builder.add_conditional_edges(
            "supervisor",
            route_supervisor,
            {
                "file_unzipping_agent": "file_unzipping_agent",
                "csv_mapping_agent": "csv_mapping_agent",
                END: END,
            },
        )
        # builder.add_edge("return_state", END)
        builder.add_conditional_edges(
            "file_unzipping_agent",
            route_agent,
            {
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            "csv_mapping_agent",
            route_agent,
            {
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )

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
        thread_id = str(uuid.uuid4())
        input_state = {
            "messages": [HumanMessage(content=input_message)],
            "tool_output": "",
            "task_description": input_message,
        }

        async for chunk in self.__graph.astream(
            input_state,
            config={"configurable": {"thread_id": thread_id}},
        ):
            self._pretty_print_messages(chunk, last_message=True)

        result = chunk
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result
