from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph
from src.layers.core_logic_layer.logging import logger

from src.layers.data_access_layer.postgres.postgres import Postgres


class WorkflowRunner:
    def __init__(self, postgres: Postgres):
        self.postgres = postgres

    async def run_workflow(
        self, workflow_builder: StateGraph, input_message: str, thread_id: str
    ) -> dict:
        try:
            async with AsyncPostgresSaver.from_conn_string(
                conn_string=self.postgres.get_conn_string()
            ) as checkpointer:
                table_exists = await self.postgres.table_exists("checkpoints")

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

                compiled_graph_with_checkpointer = workflow_builder.compile(
                    checkpointer=checkpointer
                )
                logger.info("Graph re-compiled with PostgresSaver checkpointer.")

                input_state = {"messages": [HumanMessage(content=input_message)]}

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
                        content="I'm sorry, but I couldn't process your request due to an internal error."
                    )
                ]
            }
