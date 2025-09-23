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
from src.layers.core_logic_layer.settings.streamlit_streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.core_logic_layer.settings.postgresql_settings import PostgreSQLSettings
from src.layers.data_access_layer.postgresql.postgresql import PostgreSQL


class Container(containers.DeclarativeContainer):
    ai_settings = providers.Singleton(AISettings)

    streamlit_app_settings = providers.Singleton(StreamlitAppSettings)

    postgresql_settings = providers.Singleton(PostgreSQLSettings)

    llm = providers.Singleton(LLM, ai_settings=ai_settings)

    unzip_files_from_zip_archive_tool = providers.Singleton(
        UnzipFilesFromZipArchiveTool
    )

    postgresql = providers.Singleton(
        PostgreSQL, postgresql_settings=postgresql_settings
    )

    data_analysis_workflow = providers.Singleton(
        DataAnalysisWorkflow,
        streamlit_app_settings=streamlit_app_settings,
        chat_model=llm.provided.chat_model,
        unzip_files_from_zip_archive_tool=unzip_files_from_zip_archive_tool,
    )

    workflow_runner = providers.Singleton(WorkflowRunner, postgresql=postgresql)
