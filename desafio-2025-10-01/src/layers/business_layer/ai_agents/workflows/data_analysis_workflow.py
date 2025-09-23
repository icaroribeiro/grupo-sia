import functools
import re
import pandas as pd
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from src.layers.business_layer.ai_agents.models.data_analysis_state_model import (
    DataAnalysisStateModel,
)
from langchain.agents.agent_types import AgentType
from langchain.agents import AgentExecutor
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)


class DataAnalysisWorkflow:
    __WORKFLOW: StateGraph | None = None

    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings,
        chat_model: BaseChatModel,
        unzip_files_from_zip_archive_tool: UnzipFilesFromZipArchiveTool,
    ):
        self.streamlit_app_settings = streamlit_app_settings
        self.name = "data_analysis_workflow"
        self.chat_model = chat_model
        self.unzip_files_from_zip_archive_tool = unzip_files_from_zip_archive_tool
        self.delegate_to_unzip_file_agent = DataAnalysisHandoffTool(
            agent_name="unzip_file_agent",
        )
        self.delegate_to_data_analysis_agent = DataAnalysisHandoffTool(
            agent_name="data_analysis_agent",
        )
        self.__WORKFLOW = None

    @property
    def workflow(self) -> StateGraph:
        if not self.__WORKFLOW:
            self.__WORKFLOW = self.__build()
        return self.__WORKFLOW

    @staticmethod
    def persona_node(
        state: DataAnalysisStateModel,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> DataAnalysisStateModel:
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

    def data_analysis_agent(
        self,
        state: DataAnalysisStateModel,
        name: str,
        prompt: str,
    ) -> DataAnalysisStateModel:
        # logger.info(f"Calling {name}...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")

        csv_file_paths = state.get("csv_file_paths", [])
        if not csv_file_paths:
            logger.warning("No csv file paths found in state. Skipping data analysis.")
        #     return {"messages": messages}

        dataframes: list[pd.DataFrame] = []
        for csv_file_path in csv_file_paths:
            dataframes.append(pd.read_csv(filepath_or_buffer=csv_file_path))
        if len(dataframes):
            logger.warning(f"{len(dataframes)} dataframes read for data analysis.")

        agent_executor: AgentExecutor = create_pandas_dataframe_agent(
            llm=self.chat_model,
            df=dataframes,
            # agent_type="tool-calling",
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            prefix=prompt,
            verbose=True,
        )

        response = agent_executor.invoke(messages)
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

        response_dict = agent_executor.invoke(messages)
        final_output = response_dict.get("output", "No response generated.")
        new_messages = messages + [AIMessage(content=final_output)]
        return {"messages": new_messages}

    @staticmethod
    def tool_output_node(state: DataAnalysisStateModel):
        # messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        last_message = state["messages"][-1]
        logger.info(f"Last message: {last_message}")

        if "csv_file_paths" in last_message.content:
            pattern = r"csv_file_paths:(.+)"
            match = re.search(pattern, last_message.content)
            if match:
                csv_file_paths_str = match.group(1)
                try:
                    csv_file_paths = eval(csv_file_paths_str)
                    state["csv_file_paths"] = csv_file_paths
                except Exception as e:
                    logger.error(f"Error parsing csv file paths: {e}")
        return state

    @staticmethod
    def handoff_node(
        state: DataAnalysisStateModel,
    ) -> DataAnalysisStateModel:
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
        state: DataAnalysisStateModel,
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
        state: DataAnalysisStateModel,
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
    def route_tool_output(state: DataAnalysisStateModel) -> str:
        # logger.info("Routing from tool output...")
        # last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        return "supervisor"

    @staticmethod
    def route_handoff(state: DataAnalysisStateModel) -> str:
        # logger.info("Routing from handoff_node...")
        # last_message = state["messages"][-1]
        # logger.info(f"Last message: {last_message}")
        next_agent = state.get("next_agent", "supervisor")
        # logger.info(f"To {next_agent}...")
        return next_agent

    def __build(self) -> StateGraph:
        builder = StateGraph(state_schema=DataAnalysisStateModel)

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
                    - Your primary purpose is to manage two agents to fulfill user requests:
                        - Unzip File Agent: Use this agent exclusively for decompressing ZIP files.
                        - Data Analyst Agent: Use this agent to answer specific questions about the data.
                    INSTRUCTIONS:
                    - Based on the provided instructions, decide the next action.
                    - If the instruction is to "unzip files," hand off to the 'Unzip File Agent' and DO NOT proceed with any other task.
                    - If the instruction is a "question" about the data, hand off to the 'Data Analyst Agent'.
                    - DO NOT perform any work yourself. Your only job is to delegate.
                    CRITICAL RULES:
                    - The workflow **must end** immediately after the 'Unzip File Agent' completes its task. Do not hand off to the 'Data Analyst Agent' unless a separate, explicit data analysis question is asked.
                    - DO NOT call agents in parallel. Always assign work to one agent at a time.
                    """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_unzip_file_agent,
                        self.delegate_to_data_analysis_agent,
                    ]
                ),
            ),
        )
        builder.add_node(
            node="supervisor_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_unzip_file_agent,
                    self.delegate_to_data_analysis_agent,
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
            node="data_analysis_agent",
            action=functools.partial(
                self.data_analysis_agent,
                name="data_analysis_agent",
                prompt="""
                ROLE:
                - You're a data analysis agent.
                GOAL:
                - Your sole purpose is to respond user's question properly.
                - DO NOT perform any other tasks.
                """,
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
                "data_analysis_agent": "data_analysis_agent",
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
        builder.add_conditional_edges(
            source="data_analysis_agent",
            path=functools.partial(self.route_agent, name="data_analysis_agent"),
            path_map={
                "tools": "tools",
                "supervisor": "supervisor",
            },
        )

        return builder
