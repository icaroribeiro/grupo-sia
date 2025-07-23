from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from langchain_core.prompts import ChatPromptTemplate
from src.layers.core_logic_layer.logging import logger
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, ToolMessage  # noqa: F401

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )
from langgraph.prebuilt import create_react_agent
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.presentation_layer.rest_api.schemas.send_queries_schema import (
    SendQueryRequest,
    SendQueryResponse,
)
# from typing import AsyncGenerator

# from beanie import Document
from src.layers.business_layer.ai_agents.agents.data_analysis_worker_agent import (
    DataAnalysisWorkerAgent,
)
from src.layers.data_access_layer.postgresdb.postgresdb import PostgresDB
# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
# from src.layers.business_layer.ai_agents.agents.worker_agents import (
#     WorkerAgent_1,
#     WorkerAgent_2,
#     WorkerAgent_3,
# )
# from src.layers.business_layer.ai_agents.agents.parent_agent_1 import ParentAgent_1
# from src.layers.business_layer.ai_agents.agents.sub_agent_1 import (
#     SubAgent_1,
# )
# from src.layers.business_layer.ai_agents.graphs.subgraph_1 import Subgraph_1
# from src.layers.business_layer.ai_agents.graphs.subgraph_2 import Subgraph_2
# from src.layers.business_layer.ai_agents.graphs.parent_graph_1 import ParentGraph_1
# from src.layers.data_access_layer.mongodb.mongodb import MongoDB


router = APIRouter()


@router.post(
    "/send-query",
    response_model=SendQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def send_query(
    response: Response,
    send_query_request: SendQueryRequest,
    config: dict = Depends(Provide[Container.config]),
    postgresdb: PostgresDB = Depends(Provide[Container.postgresdb]),
    data_analysis_worker_agent: DataAnalysisWorkerAgent = Depends(
        Provide[Container.data_analysis_worker_agent]
    ),
):
    logger.info(f"send_query_request.query: {send_query_request.query}")

    toolkit = AsyncSQLDatabaseToolkit(
        postgresdb=postgresdb, llm=data_analysis_worker_agent.llm
    )
    tools = toolkit.get_tools()

    # Create LangGraph agent
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a SQL assistant. Use the provided tools to query the database and answer questions.",
            ),
            MessagesPlaceholder(variable_name="messages"),  # Use messages from state
        ]
    )
    agent = create_react_agent(data_analysis_worker_agent.llm, tools, prompt=prompt)

    input_query = "Bob Johnson is a consumer. Tell me how old is Bob Johnson?"
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": input_query}]}
    )

    # Print the result
    if "output" in result:
        print(f"Agent response: {result['output']}")
    else:
        print("Agent response: No output returned")
        print(f"Full result: {result}")
    # Example query
    # query = "Alice Smith is a consumer. Tell me how old is Alice Smith?"
    # query = "How many consumer we have in database?"
    # async for event in agent.astream(
    #     {"messages": [{"role": "user", "content": input_query}]}
    # ):
    #     for key in ["agent", "tools"]:
    #         if key in event:
    #             for message in event[key].get("messages", []):
    #                 if isinstance(message, AIMessage):
    #                     if message.content:
    #                         print(f"Agent response: {message.content}")
    #                     if message.tool_calls:
    #                         print(f"Tool call: {message.tool_calls}")
    #                 elif isinstance(message, ToolMessage):
    #                     print(
    #                         f"Tool response: {message.content} (Tool: {message.name})"
    #                     )
    # llm_with_tools = data_analysis_worker_agent.llm.bind_tools(tools=tools)

    # messages = [
    #     SystemMessage(
    #         content="""
    #         You are a SQL assistant.
    #         Use the provided tools to query the database and answer questions.
    #         Always use tools to get information when needed.
    #         """
    #     ),
    #     HumanMessage(
    #         content="Alice Smith is a consumer. Tell me how old is Alice Smith?"
    #     ),
    # ]

    # response_message = llm_with_tools.invoke(messages)

    # logger.info(f"LLM's direct response message:\n{response_message}\n")
    # if response_message.tool_calls:
    #     print("LLM made a tool call! Executing it manually...")
    #     for tool_call in response_message.tool_calls:
    #         if tool_call.name == "get_current_time":
    #             # Extract arguments and call the Python function directly
    #             tool_output = sql_db_list_tables(**tool_call.args)
    #             print(f"Tool Name: {tool_call.name}")
    #             print(f"Tool Arguments: {tool_call.args}")
    #             print(f"Tool Output: {tool_output}")

    return SendQueryResponse(answer="I have no idea")
