import functools
import os
import re
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.layers.business_layer.ai_agents.models.credit_card_fraud_analysis_state_model import (
    CreditCardFraudAnalysisStateModel,
)
from src.layers.business_layer.ai_agents.tools.credit_card_fraud_analysis_handoff_tool import (
    CreditCardFraudAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.app_settings import AppSettings


class CreditCardFraudAnalysisWorkflow(BaseWorkflow):
    def __init__(
        self,
        app_settings: AppSettings,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
    ):
        self.app_settings = app_settings
        self.name = "credit_card_fraud_analysis_team"
        self.chat_model = chat_model
        self.unzip_files_from_zip_archive_tool = unzip_files_from_zip_archive_tool
        self.delegate_to_unzip_file_agent = CreditCardFraudAnalysisHandoffTool(
            agent_name="unzip_file_agent",
        )
        self.__graph = self.__build_graph()

    @staticmethod
    def persona_node(
        state: CreditCardFraudAnalysisStateModel,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> CreditCardFraudAnalysisStateModel:
        # logger.info(f"Calling {name} persona...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        agent_chain = prompt_template | llm_with_tools
        response = agent_chain.invoke(messages)
        # logger.info(f"{name} response: {response}")

        # It's to deduplicate tool calls before updating the state by ensuring that
        # only unique tool calls (based on name and arguments) are passed to
        # the tools node.
        if hasattr(response, "tool_calls") and response.tool_calls:
            seen = set()
            unique_tool_calls = []
            for tool_call in response.tool_calls:
                tool_key = (tool_call["name"], str(tool_call["args"]))
                if tool_key not in seen:
                    seen.add(tool_key)
                    unique_tool_calls.append(tool_call)
            response.tool_calls = unique_tool_calls

        return {"messages": messages + [response]}

    @staticmethod
    def tool_output_node(state: CreditCardFraudAnalysisStateModel):
        # logger.info("Calling tool output node...")
        last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        return state

    @staticmethod
    def handoff_node(
        state: CreditCardFraudAnalysisStateModel,
    ) -> CreditCardFraudAnalysisStateModel:
        # logger.info("Calling handoff_node node...")
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        pattern = r"transfer_to_agent=(\w+)::task=(.+)"
        match = re.search(pattern, last_message.content)
        if match:
            agent_name = match.group(1)
            task_description = match.group(2)
            # logger.info(f"Parsed agent: {agent_name}, task= {task_description}")
            new_task_message = HumanMessage(content=task_description)
            return {
                "messages": state["messages"] + [new_task_message],
                "next_agent": agent_name,
            }
        logger.warning("No valid agent transfer found in handoff_node")
        return {"messages": state["messages"], "next_agent": "supervisor"}

    @staticmethod
    def route_supervisor(
        state: CreditCardFraudAnalysisStateModel,
        name: str,
    ) -> str:
        # logger.info(f"Routing from {name}...")
        last_message = state["messages"][-1]
        # logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "supervisor_tools"
        else:
            routes_to = END
        # logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def route_agent(
        state: CreditCardFraudAnalysisStateModel,
        name: str,
    ) -> str:
        # logger.info(f"Routing from {name} agent...")
        last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        routes_to: str = ""

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "tools"
        else:
            routes_to = "supervisor"

        # logger.info(f"To {routes_to}...")
        return routes_to

    @staticmethod
    def route_tool_output(state: CreditCardFraudAnalysisStateModel) -> str:
        # logger.info("Routing from tool output...")
        last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")

        if last_message.name == "unzip_files_from_zip_archive_tool":
            # After unzipping, route back to the supervisor to decide the next step
            # (which should be mapping the CSVs).
            return "supervisor"
        # elif last_message.name == "insert_records_into_database_tool":
        #     # After inserting, the task is complete.
        #     return END
        # else:
        #     # For any other tool or unexpected output, route back to the supervisor.
        #     return "supervisor"
        else:
            # For any other tool or unexpected output, route back to the supervisor.
            return END

    @staticmethod
    def route_handoff(state: CreditCardFraudAnalysisStateModel) -> str:
        # logger.info("Routing from handoff_node...")
        # last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        next_agent = state.get("next_agent", "supervisor")
        # logger.info(f"To {next_agent}...")
        return next_agent

    def __build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=CreditCardFraudAnalysisStateModel)

        builder.add_node(
            node="supervisor",
            action=functools.partial(
                self.persona_node,
                name="supervisor",
                prompt=(
                    """
                    ROLE:
                    - You're a supervisor.
                    GOAL:
                    - Your sole purpose is to manage one agent:
                        - An Unzip File Agent: Assign tasks related to unzip files from ZIP archive to this agent.
                    INSTRUCTIONS:
                    - Based on the conversation history, decide the next step.
                    - DO NOT do any work yourself.
                    CRITICAL RULES:
                    - DO NOT proceed with one task if the previous only was not completed.
                    - DO NOT perform handoffs in parallel.
                    - ALWAYS assign work to one agent at time.
                    - DO NOT call agents in parallel.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_unzip_file_agent,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="supervisor_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_unzip_file_agent,
                ]
            ),
        )
        builder.add_node("handoff_node", self.handoff_node)
        builder.add_node(
            node="unzip_file_agent",
            action=functools.partial(
                self.persona_node,
                name="unzip_file_agent",
                prompt=(
                    """
                    ROLE:
                    - You're an unzip file agent.
                    GOAL:
                    - Your sole purpose is to unzip files from ZIP archive.
                    - DO NOT perform any other tasks.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[self.unzip_files_from_zip_archive_tool]
                ),
            ),
        )
        builder.add_node(
            node="tools",
            action=ToolNode(
                tools=[
                    self.unzip_files_from_zip_archive_tool,
                ]
            ),
        )
        builder.add_node("tool_output_node", self.tool_output_node)

        builder.add_edge(start_key=START, end_key="supervisor")
        builder.add_edge(start_key="supervisor_tools", end_key="handoff_node")
        builder.add_edge(start_key="tools", end_key="tool_output_node")
        builder.add_edge(start_key="tool_output_node", end_key="supervisor")

        builder.add_conditional_edges(
            source="supervisor",
            path=functools.partial(self.route_supervisor, name="supervisor"),
            path_map={"supervisor_tools": "supervisor_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                "unzip_file_agent": "unzip_file_agent",
                "supervisor": "supervisor",
            },
        )
        builder.add_conditional_edges(
            source="unzip_file_agent",
            path=functools.partial(self.route_agent, name="unzip_file_agent"),
            path_map={
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )

        checkpointer = InMemorySaver()
        graph = builder.compile(name=self.name, checkpointer=checkpointer)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        # logger.info(graph.get_graph().draw_ascii())
        graph.get_graph().draw_mermaid_png(
            output_file_path=os.path.join(
                f"{self.app_settings.output_data_dir_path}",
                f"{self.name}.png",
            )
        )
        return graph

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
        # logger.info(f"{self.name} final result: complete.")
        return {"messages": result}
