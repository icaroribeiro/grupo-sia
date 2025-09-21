# src/run_workflow_executor_postgres.py

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph
from langchain_core.messages import convert_to_messages
from src.layers.core_logic_layer.logging import logger
from src.layers.core_logic_layer.settings import postgres_settings

from src.layers.data_access_layer.postgres.postgres import Postgres


# This is a static method and doesn't need to be in the class
def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        logger.info(pretty_message)
        return
    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    logger.info(indented)


# This is a static method and doesn't need to be in the class
def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        if len(ns) == 0:
            return
        graph_id = ns[-1].split(":")[0]
        logger.info(f"Update from subgraph {graph_id}:")
        logger.info("\n")
        is_subgraph = True
    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label
        logger.info(update_label)
        logger.info("\n")
        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]
        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        logger.info("\n")


async def run_workflow_executor(
    workflow_builder: StateGraph, input_message: str, thread_id: str
) -> dict:
    """
    Executes the LangGraph workflow using a PostgresSaver for checkpointing.
    This function is designed to be called by asyncio.run() from a synchronous context.
    """
    try:
        # Create connection string
        postgres = Postgres(postgres_settings=postgres_settings)

        # 💡 Instantiate AsyncPostgresSaver here
        async with AsyncPostgresSaver.from_conn_string(
            conn_string=postgres.get_conn_string()
        ) as checkpointer:
            # 💡 Use Streamlit's session state to track if the setup has been run
            # if "postgres_setup_done" not in st.session_state:
            #     logger.info("Setting up PostgresSaver for the first time...")
            #     await checkpointer.setup()
            #     st.session_state.postgres_setup_done = True
            #     logger.info("PostgresSaver setup complete.")
            table_exists = await postgres.table_exists("checkpoints")

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

            # 💡 Compile the graph with the checkpointer.
            compiled_graph_with_checkpointer = workflow_builder.compile(
                checkpointer=checkpointer
            )
            logger.info("Graph re-compiled with PostgresSaver checkpointer.")

            input_state = {"messages": [HumanMessage(content=input_message)]}

            # Use the astream method for asynchronous execution.
            async for chunk in compiled_graph_with_checkpointer.astream(
                input_state,
                subgraphs=True,
                config={
                    "configurable": {
                        "thread_id": thread_id,
                    }
                },
            ):
                pretty_print_messages(chunk, last_message=True)
                pass

            # Retrieve the final state and access the messages.
            final_state = await compiled_graph_with_checkpointer.aget_state(
                config={"configurable": {"thread_id": thread_id}}
            )
            result_messages = final_state.values["messages"]

            return {"messages": result_messages}

    except Exception as e:
        logger.error(
            f"Failed to execute query for thread_id '{thread_id}': {e}", exc_info=True
        )
        return {
            "messages": [
                HumanMessage(
                    content="I'm sorry, but I couldn't process your request due to an internal error."
                )
            ]
        }
