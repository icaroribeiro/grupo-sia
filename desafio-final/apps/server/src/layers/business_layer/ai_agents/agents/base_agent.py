# from langchain_core.messages import BaseMessage
# from langchain_core.runnables import Runnable
# from langchain_core.tools import BaseTool
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI
# from pydantic import BaseModel


# class BaseAgentDetails(BaseModel):
#     system_message: str

#     # role: str
#     # goal: str
#     # backstory: str
#     # File Unzipper
#     # """,
#     # goal="""
#     # Extract specified ZIP files and confirm successful extraction.
#     # """,
#     # backstory="""
#     # You are an automated file system assistant, skilled at handling compressed archives.
#     # """,
#     @classmethod
#     def create_system_message(cls) -> str:
#         return cls.system_message


# class BaseAgent:
#     def __init__(
#         self,
#         name: str,
#         llm: ChatGoogleGenerativeAI | ChatOpenAI,
#         tools: list[BaseTool],
#         system_message: str,
#     ):
#         self.__name: str = name
#         self.__llm: ChatGoogleGenerativeAI | ChatOpenAI = llm
#         self.__tools: list[BaseTool] = tools
#         self.__system_message: str = system_message

#     @classmethod
#     def llm_with_tools(self) -> Runnable[BaseMessage, BaseMessage]:
#         return self.__llm.bind_tools(self.__tools)

#     @property
#     def tools(self) -> list[BaseTool]:
#         return self.__tools

#     @property
#     def system_messagels(self) -> str:
#         return self.__system_message


# # from langchain.agents import AgentExecutor, create_openai_tools_agent
# # from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# # from langchain_core.tools import BaseTool
# # from langchain_google_genai import ChatGoogleGenerativeAI
# # from langchain_openai import ChatOpenAI


# # class BaseAgent(AgentExecutor):
# #     def __init__(
# #         self,
# #         llm: ChatGoogleGenerativeAI | ChatOpenAI,
# #         tools: list[BaseTool],
# #         system_prompt: str,
# #     ):
# #         prompt = ChatPromptTemplate.from_messages(
# #             [
# #                 (
# #                     "system",
# #                     system_prompt,
# #                 ),
# #                 MessagesPlaceholder(variable_name="messages"),
# #                 MessagesPlaceholder(variable_name="agent_scratchpad"),
# #             ]
# #         )

# #         agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
# #         super().__init__(agent=agent, tools=tools, verbose=True)
