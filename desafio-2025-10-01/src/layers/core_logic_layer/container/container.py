from dependency_injector import containers, providers
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.tools.unzip_files_from_zip_archive_tool import (
    UnzipFilesFromZipArchiveTool,
)
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.layers.core_logic_layer.settings.app_settings import AppSettings
from src.layers.core_logic_layer.settings.postgres_settings import PostgresSettings
from src.layers.data_access_layer.postgres.postgres import Postgres


class Container(containers.DeclarativeContainer):
    ai_settings = providers.Singleton(AISettings)

    app_settings = providers.Singleton(AppSettings)

    postgres_settings = providers.Singleton(PostgresSettings)

    llm = providers.Singleton(LLM, ai_settings=ai_settings)

    unzip_files_from_zip_archive_tool = providers.Singleton(
        UnzipFilesFromZipArchiveTool
    )

    postgres = providers.Singleton(Postgres, postgres_settings=postgres_settings)

    data_analysis_workflow = providers.Singleton(
        DataAnalysisWorkflow,
        app_settings=app_settings,
        chat_model=llm.provided.chat_model,
        unzip_files_from_zip_archive_tool=unzip_files_from_zip_archive_tool,
    )

    workflow_runner = providers.Singleton(WorkflowRunner, postgres=postgres)
