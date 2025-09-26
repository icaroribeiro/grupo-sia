from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel


class BaseAgent(BaseModel):
    name: str
    prompt: str
    chat_model: BaseChatModel
