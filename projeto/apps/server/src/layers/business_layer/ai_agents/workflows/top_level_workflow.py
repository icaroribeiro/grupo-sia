import functools
import os
import re
import uuid

# from server.src.layers.core_logic_layer.settings.app_settings import AppSettings
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

from src.layers.business_layer.ai_agents.models.top_level_state_model import (
    TopLevelStateModel,
)
from src.layers.business_layer.ai_agents.tools.top_level_handoff_tool import (
    TopLevelHandoffTool,
)
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)


class TopLevelWorkflow(BaseWorkflow):
    def __init__(
        self,
        app_settings,
        chat_model: BaseChatModel,
        data_ingestion_workflow: DataIngestionWorkflow,
        data_analysis_workflow: DataAnalysisWorkflow,
    ):
        self.name = "top_level_team"
        self.app_settings = app_settings
        self.chat_model = chat_model
        self.data_ingestion_workflow = data_ingestion_workflow
        self.data_analysis_workflow = data_analysis_workflow
        self.delegate_to_data_ingestion_team = TopLevelHandoffTool(
            team_name=self.data_ingestion_workflow.name,
        )
        self.delegate_to_data_analysis_team = TopLevelHandoffTool(
            team_name=self.data_analysis_workflow.name,
        )
        self.__graph = self._build_graph()

    @staticmethod
    def call_persona(
        state: TopLevelStateModel,
        name: str,
        prompt: str,
        llm_with_tools: Runnable[BaseMessage, BaseMessage],
    ) -> TopLevelStateModel:
        logger.info(f"Calling {name} persona...")
        messages = state["messages"]
        # logger.info(f"Messages: {messages}")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        agent_chain = prompt_template | llm_with_tools
        result = agent_chain.invoke(messages)
        return {"messages": messages + [result]}

    @staticmethod
    def route_manager(
        state: TopLevelStateModel,
        name: str,
    ) -> str:
        logger.info(f"Routing from {name}...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message: {last_message}")
        routes_to: str = ""
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            routes_to = "manager_tools"
        else:
            routes_to = END
        logger.info(f"To {routes_to}...")
        return routes_to

    async def call_data_ingestion_workflow(
        self, state: TopLevelStateModel
    ) -> TopLevelStateModel:
        return await self.data_ingestion_workflow.run(state=state)

    async def call_data_analysis_workflow(
        self, state: TopLevelStateModel
    ) -> TopLevelStateModel:
        return await self.data_analysis_workflow.run(state=state)
        # return await self.data_analysis_workflow.run(
        #     input_message=state["task_description"]
        # )

    @staticmethod
    def handoff_node(state: TopLevelStateModel) -> TopLevelStateModel:
        logger.info("Calling handoff_node...")
        last_message = state["messages"][-1]
        logger.info(f"Last_message.content: {last_message.content}")
        pattern = r"transfer_to_team=(\w+)::task=(.+)"
        match = re.search(pattern, last_message.content)
        if match:
            team_name = match.group(1)
            task_description = match.group(2)
            logger.info(f"Parsed team: {team_name}, task= {task_description}")
            new_task_message = HumanMessage(content=task_description)
            return {
                "messages": state["messages"] + [new_task_message],
                "next_team": team_name,
            }
        logger.warning("No valid team transfer found in handoff_node")
        return {"messages": state["messages"], "next_team": "manager"}

    # @staticmethod
    # def handoff_node(state: TopLevelStateModel) -> TopLevelStateModel:
    #     logger.info("Calling handoff_node...")
    #     last_message = state["messages"][-1]
    #     logger.info(f"Last_message.content: {last_message.content}")
    #     pattern = r"transfer_to_team=(\w+)"
    #     match = re.search(pattern, last_message.content)
    #     if match:
    #         team_name = match.group(1)
    #         logger.info(f"Parsed team: {team_name}")
    #         return {
    #             "messages": state["messages"],
    #             "next_team": team_name,
    #         }
    #     logger.warning("No valid team transfer found in handoff_node")
    #     return {"messages": state["messages"], "next_team": "manager"}

    @staticmethod
    def route_handoff(state: TopLevelStateModel) -> str:
        logger.info("Routing from handoff_node...")
        # logger.info(f"state: {state}")
        next_team = state.get("next_team", "manager")
        logger.info(f"To {next_team}...")
        return next_team

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=TopLevelStateModel)

        builder.add_node(
            node="manager",
            action=functools.partial(
                self.call_persona,
                name="manager",
                prompt=(
                    """
                ROLE:
                - You're a manager.
                GOAL:
                - Your sole purpose is to manage two teams:
                    - A Data Ingestion Team: Assign tasks related to data ingestion to this team.
                    - A Data Analysis Team: Assign tasks related to data analysis to this team.
                INSTRUCTIONS:
                - Based on the conversation history, decide the next step.
                - DO NOT do any work yourself.
                CRITICAL RULES:
                - ALWAYS assign work to one team at time.
                - DO NOT call teams in parallel.
                """
                ),
                llm_with_tools=self.chat_model.bind_tools(
                    tools=[
                        self.delegate_to_data_ingestion_team,
                        self.delegate_to_data_analysis_team,
                    ]
                ),
            ),
        )
        builder.add_node(
            node=self.data_ingestion_workflow.name,
            action=self.call_data_ingestion_workflow,
        )
        builder.add_node(
            node=self.data_analysis_workflow.name,
            action=self.call_data_analysis_workflow,
        )
        builder.add_node(
            node="manager_tools",
            action=ToolNode(
                tools=[
                    self.delegate_to_data_ingestion_team,
                    self.delegate_to_data_analysis_team,
                ]
            ),
        )
        builder.add_node(node="handoff_node", action=self.handoff_node)

        builder.add_edge(start_key=START, end_key="manager")
        builder.add_edge(start_key="manager_tools", end_key="handoff_node")
        builder.add_conditional_edges(
            source="manager",
            path=functools.partial(self.route_manager, name="manager"),
            path_map={"manager_tools": "manager_tools", END: END},
        )
        builder.add_conditional_edges(
            source="handoff_node",
            path=self.route_handoff,
            path_map={
                self.data_ingestion_workflow.name: self.data_ingestion_workflow.name,
                self.data_analysis_workflow.name: self.data_analysis_workflow.name,
                "manager": "manager",
            },
        )
        builder.add_edge(start_key=self.data_ingestion_workflow.name, end_key="manager")
        builder.add_edge(start_key=self.data_analysis_workflow.name, end_key="manager")
        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
        graph.get_graph().draw_mermaid_png(
            output_file_path=os.path.join(
                f"{self.app_settings.output_data_dir_path}",
                f"{self.name}.png",
            )
        )
        return graph

    async def run(self, input_message: str) -> TopLevelStateModel:
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
        result = chunk[1]["manager"]["messages"]
        logger.info(f"{self.name} final result: complete.")
        return result
