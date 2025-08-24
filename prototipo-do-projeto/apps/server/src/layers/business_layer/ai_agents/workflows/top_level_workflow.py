from src.layers.business_layer.ai_agents.tools.top_level_handoff_tool import (
    TopLevelHandoffTool,
)
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langgraph.graph import MessagesState
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langgraph.prebuilt import create_react_agent
import uuid
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage


class TopLevelWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        data_ingestion_team: Runnable[StateGraph, StateGraph],
        data_analysis_team: Runnable[StateGraph, StateGraph],
    ):
        self.name = "top_level_team"
        self.chat_model = chat_model
        self.data_ingestion_team = data_ingestion_team
        self.data_analysis_team = data_analysis_team
        delegate_to_data_ingestion_team = TopLevelHandoffTool(
            team_name=self.data_ingestion_team.name,
        )
        delegate_to_data_analysis_team = TopLevelHandoffTool(
            team_name=self.data_analysis_team.name,
        )
        self.manager = create_react_agent(
            model=self.chat_model,
            tools=[
                delegate_to_data_ingestion_team,
                delegate_to_data_analysis_team,
            ],
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
                - ALWAYS assign work to one team at a time.
                - DO NOT call teams in parallel.
                """
            ),
            name="manager",
        )
        self.__graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)
        builder.add_node(
            self.manager,
            destinations={
                self.data_ingestion_team.name: self.data_ingestion_team.name,
                self.data_analysis_team.name: self.data_analysis_team.name,
            },
        )
        builder.add_node(self.data_ingestion_team)
        builder.add_node(self.data_analysis_team)
        builder.add_edge(START, self.manager.name)
        builder.add_edge(self.data_ingestion_team.name, self.manager.name)
        builder.add_edge(self.data_analysis_team.name, self.manager.name)
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
        # result = chunk[1]["data_analysis_team"]["messages"]
        # print(f"result: {result}")
        result = chunk[1]["manager"]["messages"]
        print(f"result: {result}")
        # for message in result:
        #     message.pretty_print()
        # result = await self.__graph.ainvoke(
        #     input_state,
        #     config={"configurable": {"thread_id": thread_id}},
        # )
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result
