from dependency_injector import containers, providers

from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.tools.calculate_absense_days_tool import (
    CalculateAbsenseDaysTool,
)
from src.layers.business_layer.ai_agents.tools.extract_absense_return_date_tool import (
    ExtractAbsenseReturnDateTool,
)
from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
)


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    llm = providers.Singleton(LLM, ai_settings=config.ai_settings)

    extract_absense_return_date_tool = providers.Singleton(ExtractAbsenseReturnDateTool)

    calculate_absense_days_tool = providers.Singleton(CalculateAbsenseDaysTool)

    top_level_workflow = providers.Singleton(
        TopLevelWorkflow,
        chat_model=llm.provided.chat_model,
        dataframes_dict=config.dataframes_dict,
        extract_absense_return_date_tool=extract_absense_return_date_tool,
        calculate_absense_days_tool=calculate_absense_days_tool,
    )
