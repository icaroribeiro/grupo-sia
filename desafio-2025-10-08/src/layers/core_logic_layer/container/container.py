from dependency_injector import containers, providers

from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.agents.supervisor_agent import SupervisorAgent
from src.layers.business_layer.ai_agents.agents.unzip_file_agent import UnzipFileAgent
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.generate_distribution_tool import (
    GenerateDistributionTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.layers.core_logic_layer.settings.postgresql_settings import PostgreSQLSettings
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.data_access_layer.postgresql.postgresql import PostgreSQL


class Container(containers.DeclarativeContainer):
    ai_settings = providers.Singleton(AISettings)
    llm = providers.Singleton(LLM, ai_settings=ai_settings)

    streamlit_app_settings = providers.Singleton(StreamlitAppSettings)

    postgresql_settings = providers.Singleton(PostgreSQLSettings)
    postgresql = providers.Singleton(
        PostgreSQL, postgresql_settings=postgresql_settings
    )

    unzip_zip_file_tool = providers.Singleton(UnzipZipFileTool)
    generate_distribution_tool = providers.Singleton(GenerateDistributionTool)
    unzip_file_agent = providers.Singleton(
        UnzipFileAgent,
        chat_model=llm.provided.chat_model,
    )
    data_analysis_agent = providers.Singleton(
        DataAnalysisAgent,
        chat_model=llm.provided.chat_model,
    )
    supervisor_agent = providers.Singleton(
        SupervisorAgent,
        chat_model=llm.provided.chat_model,
    )
    delegate_to_unzip_file_agent_tool = providers.Singleton(
        DataAnalysisHandoffTool,
        agent_name=unzip_file_agent.provided.name,
    )
    delegate_to_data_analysis_agent_tool = providers.Singleton(
        DataAnalysisHandoffTool,
        agent_name=data_analysis_agent.provided.name,
    )
    data_analysis_workflow = providers.Singleton(
        DataAnalysisWorkflow,
        unzip_zip_file_tool=unzip_zip_file_tool,
        unzip_file_agent=unzip_file_agent,
        data_analysis_agent=data_analysis_agent,
        supervisor_agent=supervisor_agent,
        delegate_to_unzip_file_agent_tool=delegate_to_unzip_file_agent_tool,
        delegate_to_data_analysis_agent_tool=delegate_to_data_analysis_agent_tool,
        eda_tools=[generate_distribution_tool],
    )

    workflow_runner = providers.Singleton(
        WorkflowRunner,
        ai_settings=ai_settings,
        streamlit_app_settings=streamlit_app_settings,
        postgresql=postgresql,
    )
