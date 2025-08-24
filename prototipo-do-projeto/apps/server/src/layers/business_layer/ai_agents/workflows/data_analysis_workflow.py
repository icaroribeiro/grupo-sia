import uuid
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.core_logic_layer.logging import logger
from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool


class DataAnalysisWorkflow(BaseWorkflow):
    def __init__(
        self,
        chat_model: BaseChatModel,
        async_query_sql_database_tools: list[BaseTool],
    ):
        self.name = "data_analysis_team"
        self.chat_model = chat_model
        self.data_analysis_agent = create_react_agent(
            model=self.chat_model,
            tools=async_query_sql_database_tools,
            prompt=(
                """
                ROLE:
                - You're a data analysis agent.
                GOAL:
                - Your sole purpose is to analyze data. 
                - DO NOT perform any other tasks.
                """
            ),
            name="data_analysis_agent",
        )
        delegate_to_data_analysis_agent = DataAnalysisHandoffTool(
            agent_name=self.data_analysis_agent.name,
        )
        self.supervisor = create_react_agent(
            model=self.chat_model,
            tools=[
                delegate_to_data_analysis_agent,
            ],
            prompt=(
                """
                ROLE:
                - You're a supervisor.
                GOAL:
                - Your sole purpose is to manage one agent:
                    - A Data Analysis Agent: Assign tasks related to data analysis to this agent.
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
        self.__graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(state_schema=MessagesState)
        builder.add_node(
            self.supervisor,
            destinations={
                self.data_analysis_agent.name: self.data_analysis_agent.name,
            },
        )
        builder.add_node(self.data_analysis_agent)
        builder.add_edge(START, self.supervisor.name)
        builder.add_edge(self.data_analysis_agent.name, self.supervisor.name)
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
