import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import START, StateGraph
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import create_react_agent

from src.layers.business_layer.ai_agents.models.top_level_state_model import (
    TopLevelStateModel,
)
from src.layers.business_layer.ai_agents.tools.top_level_handoff_tool import (
    TopLevelHandoffTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)
from src.layers.core_logic_layer.logging import logger


class TopLevelWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        data_ingestion_workflow: DataIngestionWorkflow,
        data_analysis_workflow: DataAnalysisWorkflow,
    ):
        self.name = "top_level_workflow"
        self.chat_model = chat_model
        self.data_ingestion_workflow = data_ingestion_workflow
        self.data_analysis_workflow = data_analysis_workflow
        delegate_to_data_ingestion_workflow = TopLevelHandoffTool(
            team_name=self.data_ingestion_workflow.name,
        )
        delegate_to_data_analysis_workflow = TopLevelHandoffTool(
            team_name=self.data_analysis_workflow.name,
        )
        self.manager = create_react_agent(
            model=self.chat_model,
            tools=[
                delegate_to_data_ingestion_workflow,
                delegate_to_data_analysis_workflow,
            ],
            prompt=(
                """
                ROLE:
                - You're a manager.
                GOAL:
                - Your sole purpose is to manage two teams:
                    - A Data Ingestion Team: Assign tasks related to data ingestion to this team.
                    - A Data Analysis Team: Assign tasks related to data reporting to this team.
                INSTRUCTIONS:
                - Based on the conversation history, decide the next step.
                - DO NOT do any work yourself.
                CRITICAL RULES:
                - ALWAYS assign work to one team at time.
                - DO NOT call teams in parallel.
                """
            ),
            name="manager",
        )
        self.__graph = self._build_graph()

    async def _call_data_ingestion_workflow(
        self, state: MessagesState
    ) -> MessagesState:
        return await self.data_ingestion_workflow.run(state)

    async def _call_data_analysis_workflow(
        self, state: TopLevelStateModel
    ) -> TopLevelStateModel:
        return await self.data_analysis_workflow.run(
            input_message=state["task_description"]
        )

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)

        builder.add_node(
            node=self.manager,
            destinations={
                self.data_ingestion_workflow.name: self.data_ingestion_workflow.name,
                self.data_analysis_workflow.name: self.data_analysis_workflow.name,
            },
        )
        builder.add_node(
            node=self.data_ingestion_workflow.name,
            action=self._call_data_ingestion_workflow,
        )
        builder.add_node(
            node=self.data_analysis_workflow.name,
            action=self._call_data_analysis_workflow,
        )

        builder.add_edge(start_key=START, end_key=self.manager.name)
        builder.add_edge(
            start_key=self.data_ingestion_workflow.name, end_key=self.manager.name
        )
        builder.add_edge(
            start_key=self.data_analysis_workflow.name, end_key=self.manager.name
        )
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
        result = chunk[1]["manager"]["messages"]
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result
