# plotting_page.py
import asyncio
import uuid
import streamlit as st
from dependency_injector.wiring import inject
import json

from src.layers.core_logic_layer.logging import logger
from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from dependency_injector.wiring import Provide
from src.layers.core_logic_layer.container.container import Container


class PlottingPage:
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
        if "plotting_chat_history" not in st.session_state:
            st.session_state.plotting_chat_history = []
        if "data_ready_for_chat" not in st.session_state:
            st.session_state.data_ready_for_chat = False
        self.data_analysis_workflow = data_analysis_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("📊 Plotagem de Dados")
        st.write(
            "Faça uma pergunta ao agente e ele gerará um gráfico ou análise com a resposta."
        )

        for message in st.session_state.plotting_chat_history:
            with st.chat_message("user"):
                st.markdown(message["question"])
            with st.chat_message("assistant"):
                try:
                    chart_spec = json.loads(message["answer"])
                    st.altair_chart(chart_spec, use_container_width=True)
                except (json.JSONDecodeError, TypeError):
                    st.markdown(message["answer"])

        prompt = st.chat_input(
            "Escreva sua pergunta...",
            disabled=not st.session_state.data_ready_for_chat,
        )

        if not st.session_state.get("data_ready_for_chat", False):
            st.warning(
                "Por favor, carregue um arquivo no menu 'Upload' primeiro para habilitar a plotagem."
            )
        elif prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            self.process_plot_question(question=prompt)

    def process_plot_question(
        self,
        question: str,
    ) -> None:
        try:
            with st.spinner("💡 Gerando gráfico ou análise..."):
                input_message = f"""
                INSTRUCTIONS:
                - Perform the following tasks:
                    1. Analyze the user's question accurately: {question}
                    2. Use the provided tools to generate the requested analysis or chart.
                    3. If a chart is requested, return the JSON chart specification. Otherwise, return a clear, concise text explanation.
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
                st.session_state.plotting_chat_history.append(
                    {"question": question, "answer": final_response}
                )
                with st.chat_message("assistant"):
                    try:
                        chart_spec = json.loads(final_response)
                        st.altair_chart(chart_spec, use_container_width=True)
                    except (json.JSONDecodeError, TypeError):
                        st.markdown(final_response)
                        if tool_calls:
                            st.json(tool_calls)
        except Exception as err:
            logger.error(
                f"An error occurred when processing plot query: {err}", exc_info=True
            )
            response = "⚠️ Ocorreu um erro ao processar sua pergunta."
            st.error(response)

        st.rerun()
