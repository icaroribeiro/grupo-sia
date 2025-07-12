from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI


class DataIngestionAgent(AgentExecutor):
    def __init__(self, llm: ChatGoogleGenerativeAI, tools: list[BaseTool]):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AI agent.""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
        super().__init__(agent=agent, tools=tools, verbose=True)
