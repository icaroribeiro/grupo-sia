from dependency_injector import containers, providers

from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.credit_card_fraud_analysis_workflow import (
    CreditCardFraudAnalysisWorkflow,
)
from src.layers.data_access_layer.pandas.pandas import Pandas


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    pandas = providers.Singleton(Pandas)

    llm = providers.Singleton(LLM, ai_settings=config.ai_settings)

    unzip_files_from_zip_archive_tool = providers.Singleton(
        UnzipFilesFromZipArchiveTool
    )

    credit_card_fraud_analysis_workflow = providers.Singleton(
        CreditCardFraudAnalysisWorkflow,
        app_settings=config.app_settings,
        chat_model=llm.provided.chat_model,
        unzip_files_from_zip_archive_tool=unzip_files_from_zip_archive_tool,
    )
