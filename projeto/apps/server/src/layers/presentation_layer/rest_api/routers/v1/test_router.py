from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

# from src.layers.business_layer.ai_agents.tools.test_tools import (
#     GetIcarosAgeTool,
# )
# from langgraph.prebuilt import create_react_agent
from src.layers.business_layer.ai_agents.agents.worker_agents import WorkerAgent_1
from src.layers.business_layer.ai_agents.agents.parent_agent_1 import ParentAgent_1
from src.layers.business_layer.ai_agents.agents.sub_agent_1 import (
    SubAgent_1,
)
from src.layers.business_layer.ai_agents.graphs.parent_graph_1 import ParentGraph_1
from src.layers.business_layer.ai_agents.graphs.subgraph_1 import Subgraph_1
from src.layers.core_logic_layer.container.container import Container


router = APIRouter()


@router.post(
    "/test-1",
    status_code=status.HTTP_201_CREATED,
)
@inject
async def test_1(
    response: Response,
    config: dict = Depends(Provide[Container.config]),
    worker_agent_1: WorkerAgent_1 = Depends(Provide[Container.worker_agent_1]),
    subgraph_1: Subgraph_1 = Depends(Provide[Container.subgraph_1]),
    # parent_graph: ParentGraph = Depends(Provide[Container.parent_graph]),
):
    input_message = """
        Generate a random number"
    """
    result = await subgraph_1.run(input_message=input_message, next=worker_agent_1.name)
    print(f"Final output: {result['messages'][-1].content}")

    # def worker(state: SubgraphState):
    #     return {
    #         "messages": [
    #             worker_agent_1.llm.bind_tools(worker_agent_1.tools).invoke(
    #                 [
    #                     """
    #             You are a helpful worker tasked with creating random numbers as strings.
    #             Use the CreateRandomNumberTool to generate a random number when requested.
    #         """
    #                 ]
    #                 + state["messages"]
    #             )
    #         ]
    #     }

    # subgraph_builder = StateGraph(state_schema=MessagesState)
    # subgraph_builder.add_node(
    #     node=worker_agent_1.name,
    #     # action=worker_agent_1.llm.bind_tools(worker_agent_1.tools),
    #     action=worker,
    # )
    # subgraph_builder.add_node(node="tools", action=ToolNode(worker_agent_1.tools))
    # subgraph_builder.set_entry_point(key=worker_agent_1.name)
    # subgraph_builder.add_conditional_edges(source=worker_agent_1.name, path=tools_condition)
    # subgraph_builder.add_edge("tools", worker_agent_1.name)
    # s = subgraph_builder.compile()
    # input_messages = [HumanMessage(content=input_message)]
    # messages = s.invoke({"messages": input_messages})
    # print(messages)
    return {"status": "OK"}


@router.post(
    "/test-2",
    status_code=status.HTTP_201_CREATED,
)
@inject
async def test_2(
    response: Response,
    config: dict = Depends(Provide[Container.config]),
    subgraph_2: Subgraph_1 = Depends(Provide[Container.subgraph_2]),
    sub_agent_1: SubAgent_1 = Depends(Provide[Container.sub_agent_1]),
):
    input_message = """
        Firstly, convert the text 'ABCdRT1' in lowercase. After that, check if text
        is a palindrome.
    """
    result = await subgraph_2.run(input_message=input_message, next=sub_agent_1.name)
    print(f"Final output: {result['messages'][-1].content}")
    return {"status": "OK"}


@router.post(
    "/test-3",
    status_code=status.HTTP_201_CREATED,
)
@inject
async def test_3(
    response: Response,
    config: dict = Depends(Provide[Container.config]),
    parent_graph_1: ParentGraph_1 = Depends(Provide[Container.parent_graph_1]),
    parent_agent_1: ParentAgent_1 = Depends(Provide[Container.parent_agent_1]),
):
    input_message = """
        Firstly, convert the text 'ABCdRT1' in lowercase. After that, check if text
        is a palindrome.
    """
    result = await parent_graph_1.run(
        input_message=input_message, next=parent_agent_1.name
    )
    print(f"Final output: {result['messages'][-1].content}")
    return {"status": "OK"}
