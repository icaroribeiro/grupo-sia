from dependency_injector import containers, providers

from src.layers.business_layer.ai_agents.agents.csv_mapping_agent import CSVMappingAgent
from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.agents.data_analysis_supervisor_agent import (
    DataAnalysisSupervisorAgent,
)
from src.layers.business_layer.ai_agents.agents.data_ingestion_supervisor_agent import (
    DataIngestionSupervisorAgent,
)
from src.layers.business_layer.ai_agents.agents.insert_records_agent import (
    InsertRecordsAgent,
)
from src.layers.business_layer.ai_agents.agents.manager_agent import (
    ManagerAgent,
)
from src.layers.business_layer.ai_agents.agents.unzip_file_agent import UnzipFileAgent
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.business_layer.ai_agents.tools.data_analysis_handoff_tool import (
    DataAnalysisHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.data_ingestion_handoff_tool import (
    DataIngestionHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.top_level_handoff_tool import (
    TopLevelHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.data_ingestion_workflow import (
    DataIngestionWorkflow,
)
from src.layers.business_layer.ai_agents.workflows.top_level_workflow import (
    TopLevelWorkflow,
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
    map_csvs_to_ingestion_args_tool = providers.Singleton(MapCSVsToIngestionArgsTool)
    insert_records_into_database_tool = providers.Singleton(
        InsertRecordsIntoDatabaseTool
    )
    unzip_file_agent = providers.Singleton(
        UnzipFileAgent,
        chat_model=llm.provided.chat_model,
    )
    csv_mapping_agent = providers.Singleton(
        CSVMappingAgent, chat_model=llm.provided.chat_model
    )
    insert_records_agent = providers.Singleton(
        InsertRecordsAgent, chat_model=llm.provided.chat_model
    )
    data_ingestion_supervisor_agent = providers.Singleton(
        DataIngestionSupervisorAgent,
        chat_model=llm.provided.chat_model,
    )
    delegate_to_unzip_file_agent_tool = providers.Singleton(
        DataIngestionHandoffTool,
        agent_name=unzip_file_agent.provided.name,
    )
    delegate_to_csv_mapping_agent_tool = providers.Singleton(
        DataIngestionHandoffTool,
        agent_name=csv_mapping_agent.provided.name,
    )
    delegate_to_insert_records_agent_tool = providers.Singleton(
        DataIngestionHandoffTool,
        agent_name=insert_records_agent.provided.name,
    )
    data_ingestion_workflow = providers.Singleton(
        DataIngestionWorkflow,
        unzip_zip_file_tool=unzip_zip_file_tool,
        map_csvs_to_ingestion_args_tool=map_csvs_to_ingestion_args_tool,
        insert_records_into_database_tool=insert_records_into_database_tool,
        unzip_file_agent=unzip_file_agent,
        csv_mapping_agent=csv_mapping_agent,
        insert_records_agent=insert_records_agent,
        data_ingestion_supervisor_agent=data_ingestion_supervisor_agent,
        delegate_to_unzip_file_agent_tool=delegate_to_unzip_file_agent_tool,
        delegate_to_csv_mapping_agent_tool=delegate_to_csv_mapping_agent_tool,
        delegate_to_insert_records_agent_tool=delegate_to_insert_records_agent_tool,
    )

    async_sql_database_toolkit = providers.Singleton(
        AsyncSQLDatabaseToolkit,
        postgresql=postgresql,
        chat_model=llm.provided.chat_model,
    )
    data_analysis_agent = providers.Singleton(
        DataAnalysisAgent,
        chat_model=llm.provided.chat_model,
    )
    data_analysis_supervisor_agent = providers.Singleton(
        DataAnalysisSupervisorAgent,
        chat_model=llm.provided.chat_model,
    )
    delegate_to_data_analysis_agent_tool = providers.Singleton(
        DataAnalysisHandoffTool,
        agent_name=data_analysis_agent.provided.name,
    )
    data_analysis_workflow = providers.Singleton(
        DataAnalysisWorkflow,
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
        data_analysis_agent=data_analysis_agent,
        data_analysis_supervisor_agent=data_analysis_supervisor_agent,
        delegate_to_data_analysis_agent_tool=delegate_to_data_analysis_agent_tool,
    )

    manager_agent = providers.Singleton(
        ManagerAgent,
        chat_model=llm.provided.chat_model,
    )
    delegate_to_data_ingestion_workflow_tool = providers.Singleton(
        TopLevelHandoffTool,
        workflow_name=data_ingestion_workflow.provided.name,
    )
    delegate_to_data_analysis_workflow_tool = providers.Singleton(
        TopLevelHandoffTool,
        workflow_name=data_analysis_workflow.provided.name,
    )
    top_level_workflow = providers.Singleton(
        TopLevelWorkflow,
        data_ingestion_workflow=data_ingestion_workflow,
        data_analysis_workflow=data_analysis_workflow,
        manager_agent=manager_agent,
        delegate_to_data_ingestion_workflow_tool=delegate_to_data_ingestion_workflow_tool,
        delegate_to_data_analysis_workflow_tool=delegate_to_data_analysis_workflow_tool,
    )

    workflow_runner = providers.Singleton(
        WorkflowRunner,
        ai_settings=ai_settings,
        streamlit_app_settings=streamlit_app_settings,
        postgresql=postgresql,
    )
