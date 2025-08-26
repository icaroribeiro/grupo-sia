import uuid
from src.layers.business_layer.ai_agents.models.data_ingestion_state_model import (
    DataIngestionStateModel,
)
from src.layers.business_layer.ai_agents.tools.data_ingestion_handoff_tool import (
    DataIngestionHandoffTool,
)
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ToolMessage
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
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
from typing import Dict, Any


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

        self.file_unzipping_agent = self.chat_model.bind_tools(
            [unzip_files_from_zip_archive_tool]
        )
        self.csv_mapping_agent = self.chat_model.bind_tools(
            [map_csvs_to_ingestion_args_tool]
        )
        self.ingestion_args_agent = self.chat_model.bind_tools(
            [insert_ingestion_args_into_database_tool]
        )
        self.handoff_tools = [
            DataIngestionHandoffTool(agent_name="file_unzipping_agent"),
            DataIngestionHandoffTool(agent_name="csv_mapping_agent"),
            DataIngestionHandoffTool(agent_name="ingestion_args_agent"),
        ]
        self.supervisor = self.chat_model.bind_tools(self.handoff_tools)
        self.all_tools = [
            unzip_files_from_zip_archive_tool,
            map_csvs_to_ingestion_args_tool,
            insert_ingestion_args_into_database_tool,
        ] + self.handoff_tools
        self.__graph = self.__build_graph()

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=DataIngestionStateModel)

        def supervisor_node(state: DataIngestionStateModel) -> Dict[str, Any]:
            messages = state["messages"]
            response = self.supervisor.invoke(messages)
            if isinstance(response, ToolMessage):
                logger.info(f"Tool output: {response.content}")
                return {
                    "messages": messages + [response],
                    "tool_output": response.content,
                }
            return {"messages": messages + [response]}

        async def handle_tool_node(state: DataIngestionStateModel) -> Dict[str, Any]:
            messages = state["messages"]
            last_message = messages[-1]
            if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                return {"messages": messages}
            tool_call = last_message.tool_calls[0]
            tool_name = tool_call["name"]
            tool_call_id = tool_call["id"]
            if tool_name.startswith("transfer_to_"):
                agent_name = tool_name.replace("transfer_to_", "")
                tool_message = ToolMessage(
                    content=f"Handoff to {agent_name} complete. Task assigned: {tool_call['args'].get('task_description', '')}",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
                logger.info(f"Tool output: {tool_message.content}")
                return {
                    "messages": messages + [tool_message],
                    "tool_output": tool_message.content,
                    "task_description": tool_call["args"].get(
                        "task_description", state.get("task_description", "")
                    ),
                }
            tool_node = ToolNode(self.all_tools)
            result = await tool_node.acall(state)
            if isinstance(result, dict) and "messages" in result:
                if result["messages"] and isinstance(
                    result["messages"][-1], ToolMessage
                ):
                    logger.info(f"Tool output: {result['messages'][-1].content}")
                    return {
                        "messages": result["messages"],
                        "tool_output": result["messages"][-1].content,
                    }
            return result

        builder.add_node("supervisor", supervisor_node)
        builder.add_node(
            "file_unzipping_agent",
            lambda state: {
                "messages": state["messages"]
                + [self.file_unzipping_agent.invoke(state["messages"])]
            },
        )
        builder.add_node(
            "csv_mapping_agent",
            lambda state: {
                "messages": state["messages"]
                + [self.csv_mapping_agent.invoke(state["messages"])]
            },
        )
        builder.add_node(
            "ingestion_args_agent",
            lambda state: {
                "messages": state["messages"]
                + [self.ingestion_args_agent.invoke(state["messages"])]
            },
        )
        builder.add_node("tools", handle_tool_node)

        builder.add_edge(START, "supervisor")
        builder.add_edge("tools", "supervisor")

        def route_to_agent(state: DataIngestionStateModel):
            if not state.get("messages"):
                return END
            last_message = state["messages"][-1]
            if isinstance(last_message, ToolMessage) and last_message.name.startswith(
                "transfer_to_"
            ):
                agent_name = last_message.name.replace("transfer_to_", "")
                if agent_name in [
                    "file_unzipping_agent",
                    "csv_mapping_agent",
                    "ingestion_args_agent",
                ]:
                    return agent_name
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_name = last_message.tool_calls[0]["name"]
                if tool_name.startswith("transfer_to_"):
                    agent_name = tool_name.replace("transfer_to_", "")
                    if agent_name in [
                        "file_unzipping_agent",
                        "csv_mapping_agent",
                        "ingestion_args_agent",
                    ]:
                        return agent_name
                return "tools"
            return END

        builder.add_conditional_edges(
            "supervisor",
            route_to_agent,
            {
                "file_unzipping_agent": "file_unzipping_agent",
                "csv_mapping_agent": "csv_mapping_agent",
                "ingestion_args_agent": "ingestion_args_agent",
                "tools": "tools",
                END: END,
            },
        )

        def check_for_tool_call(state: DataIngestionStateModel):
            if not state.get("messages"):
                return "supervisor"
            last_message = state["messages"][-1]
            if isinstance(last_message, ToolMessage):
                logger.info(f"Tool output: {last_message.content}")
                state["tool_output"] = last_message.content
                return "supervisor"
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "supervisor"

        builder.add_conditional_edges(
            "file_unzipping_agent",
            check_for_tool_call,
            {"tools": "tools", "supervisor": "supervisor"},
        )
        builder.add_conditional_edges(
            "csv_mapping_agent",
            check_for_tool_call,
            {"tools": "tools", "supervisor": "supervisor"},
        )
        builder.add_conditional_edges(
            "ingestion_args_agent",
            check_for_tool_call,
            {"tools": "tools", "supervisor": "supervisor"},
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
