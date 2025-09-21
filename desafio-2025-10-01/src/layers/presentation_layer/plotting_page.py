# plotting_page.py
import asyncio
import streamlit as st
from dependency_injector.wiring import Provide, inject
import json

from src.layers.business_layer.ai_agents.workflows.data_analysis_workflow import (
    DataAnalysisWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger


class PlottingPage:
    def __init__(self) -> None:
        if "plotting_chat_history" not in st.session_state:
            st.session_state.plotting_chat_history = []

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
                    # Assuming the AI's response is a JSON string of an Altair chart spec
                    chart_spec = json.loads(message["answer"])
                    st.altair_chart(chart_spec, use_container_width=True)
                except (json.JSONDecodeError, TypeError):
                    # If it's not a valid JSON, display it as plain text
                    st.markdown(message["answer"])

        # Control the chat input based on whether a file has been uploaded and processed
        prompt = st.chat_input(
            "Type your question...",
            disabled=not st.session_state.get("data_ready_for_chat", False),
        )

        if not st.session_state.get("data_ready_for_chat", False):
            st.warning(
                "Por favor, carregue um arquivo no menu 'Upload' primeiro para habilitar a plotagem."
            )
        elif prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            self.process_plot_query(question=prompt)

    @inject
    def process_plot_query(
        self,
        question: str,
        data_analysis_workflow: DataAnalysisWorkflow = Provide[
            Container.data_analysis_workflow
        ],
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
                    data_analysis_workflow.run(input_message=input_message)
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
