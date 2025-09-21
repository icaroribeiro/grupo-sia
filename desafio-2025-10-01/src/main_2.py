# src/main_2.py
import streamlit as st
import asyncio
import uuid

from src.layers.core_logic_layer.logging import logger
from src.workflow import workflow  # The LangGraph builder
from src.run_workflow_executor_postgres import run_workflow_executor  # The new executor

st.set_page_config(
    page_title="Preetam's BioBot – Your Personal AI Assistant", page_icon="🤖"
)
st.title("About Preetam 🙋‍♂️")

# --- Session State Initialization and Management ---

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_thread_id" not in st.session_state:
    st.session_state.session_thread_id = str(uuid.uuid4())
    logger.info(
        f"New session started with thread_id: {st.session_state.session_thread_id}"
    )

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write("Hello, you can ask me anything about Preetam 👋")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input and Response Generation ---

if query_text := st.chat_input("Ask away!"):
    with st.chat_message("user"):
        st.markdown(query_text)

    st.session_state.messages.append({"role": "user", "content": query_text})

    with st.spinner("Thinking..."):
        try:
            # 💡 Call the new executor function to run the async workflow.
            response = asyncio.run(
                run_workflow_executor(
                    workflow,  # Pass the uncompiled graph
                    query_text,
                    st.session_state.session_thread_id,
                )
            )
            response_content = response["messages"][-1].content
        except Exception as e:
            logger.error(
                f"Error executing RAG query in Streamlit app: {e}", exc_info=True
            )
            response_content = "I apologize, but I encountered an unexpected error. Please try asking again."

    with st.chat_message("assistant"):
        st.markdown(response_content)

    st.session_state.messages.append({"role": "assistant", "content": response_content})
