import uuid
import streamlit as st
import asyncio
from dependency_injector.wiring import inject
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.core_logic_layer.logging import logger
from dependency_injector.wiring import Provide
from src.layers.core_logic_layer.container.container import Container


class ChatPage:
    @inject
    def __init__(
        self,
        data_analysis_workflow: DataAnalysisWorkflow = Provide[
            Container.data_analysis_workflow
        ],
        workflow_runner: WorkflowRunner = Provide[Container.workflow_runner],
    ) -> None:
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = str(uuid.uuid4())
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "data_ready_for_chat" not in st.session_state:
            st.session_state.data_ready_for_chat = False
        self.data_analysis_workflow = data_analysis_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("💬 Converse com o Agente")
        st.write("Faça uma pergunta ao agente sobre os dados.")

        for message in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(message["question"])
            with st.chat_message("assistant"):
                st.markdown(message["answer"])

        query = st.chat_input(
            "Escreva sua pergunta...",
            disabled=not st.session_state.data_ready_for_chat,
        )

        if not st.session_state.data_ready_for_chat:
            st.warning(
                "Por favor, carregue um arquivo no menu 'Upload' primeiro para habilitar o bate-papo."
            )
        elif query:
            with st.chat_message("user"):
                st.markdown(query)
            self.process_chat_query(query=query)

    def process_chat_query(
        self,
        query: str,
    ) -> None:
        try:
            with st.spinner("💡 Gerando resposta..."):
                input_message = f"""
                INSTRUCTIONS:
                    - Perform the following tasks:
                    1. Analyze the user's question accurately: {query}
                    2. Respond the user's question objectivelly.
                CRITICAL RULES:
                    - DO NOT assign any of these tasks to Unzip file Agent.
                """
                response = asyncio.run(
                    self.workflow_runner.run_workflow(
                        self.data_analysis_workflow.workflow,
                        input_message,
                        st.session_state.session_thread_id,
                    )
                )
                final_response = response["messages"][-1].content
                tool_calls = response["messages"][-1].additional_kwargs.get(
                    "tool_calls", []
                )
                st.session_state.chat_history.append(
                    {"question": query, "answer": final_response}
                )
                with st.chat_message("assistant"):
                    st.markdown(final_response)
                    if tool_calls:
                        st.json(tool_calls)
        except Exception as err:
            logger.error(
                f"An error occurred when processing user query: {err}", exc_info=True
            )
            response = "⚠️ Ocorreu um erro ao processar sua pergunta."
            st.error(response)

        st.rerun()
