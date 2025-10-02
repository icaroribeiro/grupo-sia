import os
import time

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from openai import RateLimitError

from src.layers.business_layer.ai_agents.workflows.base_workflow import BaseWorkflow
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings.ai_settings import AISettings
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.data_access_layer.postgresql.postgresql import PostgreSQL


class WorkflowRunner:
    def __init__(
        self,
        ai_settings: AISettings,
        streamlit_app_settings: StreamlitAppSettings,
        postgresql: PostgreSQL,
    ):
        self.ai_settings = ai_settings
        self.streamlit_app_settings = streamlit_app_settings
        self.postgresql = postgresql

    async def run_workflow(
        self, workflow: BaseWorkflow, input_message: str, thread_id: str
    ) -> dict:
        for attempt in range(self.ai_settings.llm_max_retries):
            try:
                try:
                    async with AsyncPostgresSaver.from_conn_string(
                        conn_string=self.postgresql.get_conn_string()
                    ) as checkpointer:
                        table_exists = await self.postgresql.table_exists("checkpoints")

                        if not table_exists:
                            logger.info(
                                "Setting up PostgresSaver: 'checkpoints' table not found. Creating it..."
                            )
                            await checkpointer.setup()
                            logger.info("PostgresSaver setup complete.")
                        else:
                            logger.info(
                                "PostgresSaver setup skipped. 'checkpoints' table already exists."
                            )

                        compiled_graph_with_checkpointer = workflow.workflow.compile(
                            checkpointer=checkpointer
                        )
                        logger.info(
                            "Graph re-compiled with PostgresSaver checkpointer."
                        )
                        logger.info(f"Graph {workflow.name} compiled successfully!")
                        logger.info(
                            f"Nodes in graph: {compiled_graph_with_checkpointer.nodes.keys()}"
                        )
                        logger.info(
                            compiled_graph_with_checkpointer.get_graph().draw_ascii()
                        )
                        compiled_graph_with_checkpointer.get_graph().draw_mermaid_png(
                            output_file_path=os.path.join(
                                f"{self.streamlit_app_settings.output_data_dir_path}",
                                f"{workflow.name}.png",
                            )
                        )
                        input_state = {
                            "messages": [HumanMessage(content=input_message)]
                        }
                        async for chunk in compiled_graph_with_checkpointer.astream(
                            input_state,
                            subgraphs=True,
                            config={
                                "configurable": {
                                    "thread_id": thread_id,
                                }
                            },
                        ):
                            pass
                        final_state = await compiled_graph_with_checkpointer.aget_state(
                            config={"configurable": {"thread_id": thread_id}}
                        )
                        result_messages = final_state.values["messages"]
                        return {"messages": result_messages}
                except Exception as e:
                    logger.error(
                        f"Failed to execute query for thread_id '{thread_id}': {e}",
                        exc_info=True,
                    )
                    return {
                        "messages": [
                            HumanMessage(
                                content="Lamento, mas não consegui processar o seu pedido devido a um erro interno."
                            )
                        ]
                    }
            except RateLimitError as error:
                if attempt < self.ai_settings.llm_max_retries - 1:
                    logger.info(
                        f"Rate limit hit, retrying in {self.ai_settings.llm_retry_delay}s..."
                    )
                    time.sleep(self.ai_settings.llm_retry_delay)
                else:
                    logger.error(
                        f"Rate limit error: {error}",
                    )
                    raise error
