from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.layers.business_layer.ai_agents.models.agent import Agent
from src.layers.business_layer.ai_agents.models.agent_state import AgentState
from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow


class TestWorkflow(BaseWorkflow):
    def __init__(self, agent_1: Agent):
        self.llm = agent_1.llm
        self.__graph = self.create_graph(agent_1=agent_1)

    # def _agent(self, state: AgentState) -> AgentState:
    #     messages = state["messages"]
    #     response = self.llm.invoke(messages)
    #     return {"messages": messages + [response]}

    # async def _tools(self, state: AgentState) -> AgentState:
    #     self.logger.debug("Running tools node")
    #     messages = state["messages"]
    #     last_message = messages[-1]

    #     if hasattr(last_message, "tool_calls") and last_message.tool_calls:
    #         tool = LowerCaseTool()
    #         results = []
    #         for tool_call in last_message.tool_calls:
    #             self.logger.info(
    #                 f"Executing tool call: {tool_call['name']} with args: {tool_call['args']}"
    #             )
    #             result = await tool.acall(**tool_call["args"])
    #             results.append(
    #                 AIMessage(content=str(result), tool_call_id=tool_call["id"])
    #             )
    #         self.logger.debug(f"Tool execution results: {results}")
    #         return {"messages": messages + results}
    #     return state

    def create_graph(self, agent_1: Agent) -> StateGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node(
            agent_1.name,
            self.create_agent_node(
                prompt=agent_1.prompt,
                llm_with_tools=agent_1.llm.bind_tools(agent_1.tools),
            ),
        )
        workflow.add_node("tools", ToolNode(agent_1.tools))
        # workflow.set_entry_point(agent_1.name)
        # workflow.add_conditional_edges(
        #     agent_1.name, self.should_continue, {"tools": "tools", END: END}
        # )
        workflow.add_edge("tools", agent_1.name)

        # Supervisor
        members = [agent_1.name]
        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the"
            " following workers:  {members}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH."
        )

        options = ["FINISH"] + members
        function_def = {
            "name": "route",
            "description": "Select the next role.",
            "parameters": {
                "title": "routeSchema",
                "type": "object",
                "properties": {
                    "next": {
                        "title": "Next",
                        "anyOf": [
                            {"enum": options},
                        ],
                    }
                },
                "required": ["next"],
            },
        }
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    "Given the conversation above, who should act next?"
                    " Or should we FINISH? Select one of: {options}",
                ),
            ]
        ).partial(options=str(options), members=", ".join(members))

        supervisor_chain = (
            prompt
            | agent_1.llm.bind_functions(
                functions=[function_def], function_call="route"
            )
            | JsonOutputFunctionsParser()
        )
        workflow.add_node("supervisor", supervisor_chain)

        for member in members:
            workflow.add_edge(member, "supervisor")

        conditional_map = {k: k for k in members}
        conditional_map["FINISH"] = END
        workflow.add_conditional_edges(
            "supervisor", lambda x: x["next"], conditional_map
        )
        workflow.set_entry_point("supervisor")
        return workflow.compile()
