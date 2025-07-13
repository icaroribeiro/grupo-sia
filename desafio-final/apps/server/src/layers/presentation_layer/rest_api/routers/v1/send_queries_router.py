from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )

# from langgraph.prebuilt import create_react_agent
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.send_queries_schema import (
    SendQueryRequest,
    SendQueryResponse,
)

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
    llm_resource: ChatOpenAI | ChatGoogleGenerativeAI = Depends(
        Provide[Container.llm_resource]
    ),
    config: dict = Depends(Provide[Container.config]),
):
    logger.info(f"send_query_request.query: {send_query_request.query}")

    tools = [GetIcarosAgeTool()]
    tool_node = ToolNode(tools)
    llm_with_tools = llm_resource.bind_tools(tools)

    # System message
    sys_msg = SystemMessage(
        content="You are a helpful assistant tasked with finding Icaro's age."
    )

    # Node
    def assistant(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

    # Graph
    builder = StateGraph(MessagesState)

    # Define nodes: these do the work
    builder.add_node("assistant", assistant)
    builder.add_node("tools", tool_node)

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
        # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
        tools_condition,
    )
    # tools node sends the information back to the assistant
    builder.add_edge("tools", "assistant")
    graph = builder.compile()

    # Show
    display(Image(graph.get_graph(xray=True).draw_mermaid_png()))

    input_messages = [HumanMessage(content="What is Icaro's age?")]
    messages = graph.invoke({"messages": input_messages})
    for m in messages["messages"]:
        logger.info(f"message: {m.pretty_print()}")

    # result = llm_with_tools.invoke(system_prompt)
    # print(f"result: {result}")
    # print(f"result.tool_calls: {result.tool_calls}")

    # query = "What is Icaro's age?"
    # response = llm_with_tools.invoke(query)
    # print(f"response: {response}")

    # Using pre-built agent
    # system_prompt = """Act as a helpful assistant.
    #     Given only the tools at your disposal, mention tool calls for the following tasks:
    #         1. What is Icaro's age?
    #     """
    # agent = create_react_agent(model=llm_resource, tools=tools, prompt=system_prompt)
    # def print_stream(stream):
    #     for s in stream:
    #         message = s["messages"][-1]
    #         if isinstance(message, tuple):
    #             print(message)
    #         else:
    #             message.pretty_print()
    # inputs = {"messages": [("user", "What is Icaro's age?")]}
    # response = agent.stream(inputs, stream_mode="values")
    # print(f"response: {response}")
    # print_stream(agent.stream(inputs, stream_mode="values"))

    return SendQueryResponse(answer="")
