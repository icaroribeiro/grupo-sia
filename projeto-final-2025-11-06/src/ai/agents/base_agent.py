from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel


class BaseAgent(BaseModel):
    name: str
    prompt: str
    chat_model: BaseChatModel
