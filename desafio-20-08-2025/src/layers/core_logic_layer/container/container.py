from dependency_injector import containers, providers

from src.layers.business_layer.ai_agents.llm.llm import LLM


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    llm = providers.Singleton(LLM, ai_settings=config.ai_settings)
