from dependency_injector import containers, providers

from src.layers.business_layer.ai_agents.agents.csv_mapping_agent import CSVMappingAgent
from src.layers.business_layer.ai_agents.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.layers.business_layer.ai_agents.agents.insert_records_agent import (
    InsertRecordsAgent,
)
from src.layers.business_layer.ai_agents.agents.supervisor_agent import SupervisorAgent
from src.layers.business_layer.ai_agents.agents.unzip_file_agent import UnzipFileAgent
from src.layers.business_layer.ai_agents.llm.llm import LLM
from src.layers.business_layer.ai_agents.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.layers.business_layer.ai_agents.tools.invoice_mgmt_handoff_tool import (
    InvoiceMgmtHandoffTool,
)
from src.layers.business_layer.ai_agents.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.layers.business_layer.ai_agents.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.layers.business_layer.ai_agents.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.layers.core_logic_layer.settings.postgresql_db_settings import (
    PostgreSQLDBSettings,
)
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.data_access_layer.db.postgresql.postgresql import PostgreSQL


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Settings
    ai_settings = providers.Singleton(AISettings)
    postgresql_db_settings = providers.Singleton(PostgreSQLDBSettings)
    streamlit_app_settings = providers.Singleton(StreamlitAppSettings)

    # LLM
    llm = providers.Singleton(LLM, ai_settings=ai_settings)

    # Database
    postgresql = providers.Singleton(
        PostgreSQL, postgresql_db_settings=postgresql_db_settings
    )

    # Agents
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
    data_analysis_agent = providers.Singleton(
        DataAnalysisAgent,
        chat_model=llm.provided.chat_model,
    )
    supervisor_agent = providers.Singleton(
        SupervisorAgent,
        chat_model=llm.provided.chat_model,
    )

    # Tools
    unzip_zip_file_tool = providers.Singleton(UnzipZipFileTool)
    map_csvs_to_ingestion_args_tool = providers.Singleton(
        MapCSVsToIngestionArgsTool, ingestion_config_dict=config.ingestion_config_dict
    )
    insert_records_into_database_tool = providers.Singleton(
        InsertRecordsIntoDatabaseTool,
        postgresql=postgresql,
        sqlalchemy_model_by_table_name=config.sqlalchemy_model_by_table_name,
        ingestion_config_dict=config.ingestion_config_dict,
    )
    async_sql_database_toolkit = providers.Singleton(
        AsyncSQLDatabaseToolkit,
        postgresql=postgresql,
        chat_model=llm.provided.chat_model,
    )

    # Handoff tools
    delegate_to_unzip_file_agent_tool = providers.Singleton(
        InvoiceMgmtHandoffTool,
        agent_name=unzip_file_agent.provided.name,
    )
    delegate_to_csv_mapping_agent_tool = providers.Singleton(
        InvoiceMgmtHandoffTool,
        agent_name=csv_mapping_agent.provided.name,
    )
    delegate_to_insert_records_agent_tool = providers.Singleton(
        InvoiceMgmtHandoffTool,
        agent_name=insert_records_agent.provided.name,
    )
    delegate_to_data_analysis_agent_tool = providers.Singleton(
        InvoiceMgmtHandoffTool,
        agent_name=data_analysis_agent.provided.name,
    )

    # Workflow
    invoice_mgmt_workflow = providers.Singleton(
        InvoiceMgmtWorkflow,
        unzip_file_agent=unzip_file_agent,
        csv_mapping_agent=csv_mapping_agent,
        insert_records_agent=insert_records_agent,
        data_analysis_agent=data_analysis_agent,
        supervisor_agent=supervisor_agent,
        unzip_zip_file_tool=unzip_zip_file_tool,
        map_csvs_to_ingestion_args_tool=map_csvs_to_ingestion_args_tool,
        insert_records_into_database_tool=insert_records_into_database_tool,
        data_analysis_tools=async_sql_database_toolkit.provided.get_tools.call(),
        delegate_to_unzip_file_agent_tool=delegate_to_unzip_file_agent_tool,
        delegate_to_csv_mapping_agent_tool=delegate_to_csv_mapping_agent_tool,
        delegate_to_insert_records_agent_tool=delegate_to_insert_records_agent_tool,
        delegate_to_data_analysis_agent_tool=delegate_to_data_analysis_agent_tool,
    )

    # Workflow runner
    workflow_runner = providers.Singleton(
        WorkflowRunner,
        ai_settings=ai_settings,
        streamlit_app_settings=streamlit_app_settings,
        postgresql=postgresql,
    )
