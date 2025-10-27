from dependency_injector import containers, providers

from src.streamlit_app_layers.ai_layer.agents.csv_mapping_agent import (
    CSVMappingAgent,
)
from src.streamlit_app_layers.ai_layer.agents.data_analysis_agent import (
    DataAnalysisAgent,
)
from src.streamlit_app_layers.ai_layer.agents.insert_records_agent import (
    InsertRecordsAgent,
)
from src.streamlit_app_layers.ai_layer.agents.supervisor_agent import (
    SupervisorAgent,
)
from src.streamlit_app_layers.ai_layer.agents.unzip_file_agent import (
    UnzipFileAgent,
)
from src.streamlit_app_layers.ai_layer.llm.llm import LLM
from src.streamlit_app_layers.ai_layer.toolkits.async_sql_database_toolkit import (
    AsyncSQLDatabaseToolkit,
)
from src.streamlit_app_layers.ai_layer.tools.generate_bar_plot_tool import (
    GenerateBarPlotTool,
)
from src.streamlit_app_layers.ai_layer.tools.get_detailed_table_schemas_tool import (
    GetDetailedTableSchemasTool,
)
from src.streamlit_app_layers.ai_layer.tools.invoice_mgmt_handoff_tool import (
    InvoiceMgmtHandoffTool,
)
from src.streamlit_app_layers.ai_layer.tools.insert_records_into_database_tool import (
    InsertRecordsIntoDatabaseTool,
)
from src.streamlit_app_layers.ai_layer.tools.generate_distribution_plot_tool import (
    GenerateDistributionPlotTool,
)
from src.streamlit_app_layers.ai_layer.tools.map_csvs_to_ingestion_args_tool import (
    MapCSVsToIngestionArgsTool,
)
from src.streamlit_app_layers.ai_layer.tools.unzip_zip_file_tool import (
    UnzipZipFileTool,
)
from src.streamlit_app_layers.ai_layer.workflow_runner import WorkflowRunner
from src.streamlit_app_layers.ai_layer.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.streamlit_app_layers.settings_layer.ai_settings import AISettings
from src.streamlit_app_layers.settings_layer.postgresql_db_settings import (
    PostgreSQLDBSettings,
)
from src.streamlit_app_layers.settings_layer.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.streamlit_app_layers.data_access_layer.db.postgresql import PostgreSQL


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
    get_detailed_table_schemas_tool = providers.Singleton(
        GetDetailedTableSchemasTool,
        postgresql=postgresql,
    )
    generate_bar_plot_tool = providers.Singleton(
        GenerateBarPlotTool,
        postgresql=postgresql,
    )
    generate_distribution_plot_tool = providers.Singleton(
        GenerateDistributionPlotTool,
        postgresql=postgresql,
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
        async_sql_database_tools=async_sql_database_toolkit.provided.get_tools.call(),
        get_detailed_table_schemas_tool=get_detailed_table_schemas_tool,
        generate_bar_plot_tool=generate_bar_plot_tool,
        generate_distribution_plot_tool=generate_distribution_plot_tool,
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
