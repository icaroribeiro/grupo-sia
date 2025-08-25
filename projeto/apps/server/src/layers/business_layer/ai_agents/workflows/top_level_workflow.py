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
from langchain_core.messages import HumanMessage, AIMessage


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
            tools=[delegate_to_data_ingestion_team, delegate_to_data_analysis_team],
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

    async def _call_subgraph(
        self, state: MessagesState, subgraph: Runnable[StateGraph, StateGraph]
    ) -> MessagesState:
        team_name = subgraph.name
        logger.info(f"Preparing to call subgraph: '{team_name}'")
        task_description = None

        if len(state["messages"]) > 1:
            previous_message = state["messages"][-2]
            if isinstance(previous_message, AIMessage) and previous_message.tool_calls:
                tool_name_to_find = f"transfer_to_{team_name}"
                for tool_call in previous_message.tool_calls:
                    if tool_call.get("name") == tool_name_to_find:
                        task_description = tool_call.get("args", {}).get(
                            "task_description"
                        )
                        logger.info(f"Found task for '{team_name}' in tool call.")
                        break

        if not task_description:
            message = f"Error: Could not find a valid task for '{team_name}' in the manager's tool call."
            logger.error(message)
            return {"messages": state["messages"] + [HumanMessage(content=message)]}

        logger.info(f"Invoking {team_name} with task: '{task_description}'")
        try:
            result = await subgraph.ainvoke(
                {"messages": [HumanMessage(content=task_description)]}
            )
            subgraph_messages = result.get("messages", [])
            return {"messages": state["messages"] + subgraph_messages}
        except Exception as error:
            message = f"Error during {team_name} execution: {error}"
            logger.error(message, exc_info=True)
            return {"messages": state["messages"] + [HumanMessage(content=message)]}

    async def call_data_ingestion_team(self, state: MessagesState) -> MessagesState:
        """Node action that invokes the Data Ingestion Team subgraph."""
        return await self._call_subgraph(state, self.data_ingestion_team)

    async def call_data_analysis_team(self, state: MessagesState) -> MessagesState:
        """Node action that invokes the Data Analysis Team subgraph."""
        return await self._call_subgraph(state, self.data_analysis_team)

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)

        builder.add_node(
            self.manager,
            destinations={
                self.data_ingestion_team.name: self.data_ingestion_team.name,
                self.data_analysis_team.name: self.data_analysis_team.name,
            },
        )
        builder.add_node(
            self.data_ingestion_team.name,
            action=self.call_data_ingestion_team,
        )
        builder.add_node(
            self.data_analysis_team.name,
            action=self.call_data_analysis_team,
        )

        builder.add_edge(START, self.manager.name)
        builder.add_edge(self.data_ingestion_team.name, self.manager.name)
        builder.add_edge(self.data_analysis_team.name, self.manager.name)
        graph = builder.compile(name=self.name)
        logger.info(f"Graph {self.name} compiled successfully!")
        logger.info(f"Nodes in graph: {graph.nodes.keys()}")
        logger.info(graph.get_graph().draw_ascii())
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
        result = chunk[1]["manager"]["messages"]
        # for message in result:
        #     message.pretty_print()
        # result = await self.__graph.ainvoke(
        #     input_state,
        #     config={"configurable": {"thread_id": thread_id}},
        # )
        final_message = f"{self.name} complete."
        logger.info(f"{self.name} final result: {final_message}")
        return result
