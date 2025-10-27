import asyncio
import json
import re
from typing import Any

import streamlit as st
from dependency_injector.wiring import Provide, inject

from src.streamlit_app_layers.ai_layer.workflow_runner import WorkflowRunner
from src.streamlit_app_layers.ai_layer.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.streamlit_app_layers.core_layer.container.container import Container
from src.streamlit_app_layers.core_layer.logging import logger
from src.streamlit_app_layers.settings_layer.streamlit_app_settings import (
    StreamlitAppSettings,
)


class ChatPage:
    @inject
    def __init__(
        self,
        streamlit_app_settings: StreamlitAppSettings = Provide[
            Container.streamlit_app_settings
        ],
        invoice_mgmt_workflow: InvoiceMgmtWorkflow = Provide[
            Container.invoice_mgmt_workflow
        ],
        workflow_runner: WorkflowRunner = Provide[Container.workflow_runner],
    ) -> None:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "chat_enabled" not in st.session_state:
            st.session_state.chat_enabled = True
        self.streamlit_app_settings = streamlit_app_settings
        self.invoice_mgmt_workflow = invoice_mgmt_workflow
        self.workflow_runner = workflow_runner

    def show(self) -> None:
        st.title("💬 Bate-Papo com o Agente de IA")
        st.markdown(
            "Use este chat para interagir com o seu agente de IA, que pode analisar ou executar tarefas no sistema."
        )

        chat_container = st.container()
        with chat_container:
            if not st.session_state.chat_history:
                st.info("Olá! Como posso ajudar você hoje?")

            for message in st.session_state.chat_history:
                with st.chat_message("user"):
                    st.markdown(message["question"])
                with st.chat_message("assistant"):
                    response_data = self.__extract_json_from_content(message["answer"])
                    self.__display_assistant_response(response_data)

        prompt = st.chat_input(
            "Digite sua mensagem...",
            disabled=not st.session_state.chat_enabled,
        )

        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            self.process_chat_question(question=prompt)

    def process_chat_question(self, question: str) -> None:
        try:
            status_placeholder = st.empty()
            status_placeholder.info(
                "💡 Gerando resposta com o fluxo de trabalho do agente..."
            )

            input_message = f"""
            INSTRUCTIONS:
            - A user has submitted the following query from the chat interface: '{question}'
            - Analyze this query and route it to the most appropriate specialist agent based on your internal instructions to generate a final response.

            CRITICAL RULES:
            - When receive a response, always answer the query in the same language in which it was asked.
            """
            response = asyncio.run(
                self.workflow_runner.run_workflow(
                    self.invoice_mgmt_workflow,
                    input_message,
                    st.session_state.get("session_thread_id", "dummy_chat_thread"),
                )
            )

            final_message = response["messages"][-1]
            final_response_str = final_message.content

            status_placeholder.empty()

            response_data = self.__extract_json_from_content(final_response_str)
            with st.chat_message("assistant"):
                self.__display_assistant_response(response_data)

            st.session_state.chat_history.append(
                {"question": question, "answer": final_response_str}
            )
        except Exception as error:
            logger.error(
                f"An UNEXPECTED error occurred when processing chat query: {error}",
                exc_info=True,
            )
            final_response = "⚠️ Ocorreu um erro catastrófico ao processar sua pergunta. Por favor, tente novamente."

            status_placeholder.empty()
            with st.chat_message("assistant"):
                st.error(final_response)

            st.session_state.chat_history.append(
                {"question": question, "answer": final_response}
            )
        st.rerun()

    def __display_assistant_response(self, response_data: Any) -> None:
        try:
            if isinstance(response_data, dict):
                if "text" in response_data:
                    st.markdown(response_data["text"])

                if "chart" in response_data:
                    chart_spec = response_data.get("chart")
                    if chart_spec:
                        chart = self.__unescape_dict(chart_spec)
                        st.vega_lite_chart(chart, use_container_width=True)

                if "description" in response_data:
                    description_spec = response_data.get(
                        "description", "Análise Concluída."
                    )
                    if description_spec:
                        description = description_spec
                        st.markdown(f"**Resultado:** {description}")

                if "error" in response_data:
                    st.error(response_data["error"])
            else:
                st.markdown(response_data)
        except Exception as error:
            logger.error(f"Error displaying assistant response: {error}")
            st.error("Ocorreu um erro ao exibir a resposta do assistente.")
            st.json(response_data)

    @staticmethod
    def __extract_json_from_content(content_str: str) -> dict | str:
        json_pattern = r"content='(\{.*\})'"
        json_match = re.search(json_pattern, content_str, re.DOTALL)

        json_str = None
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content_str.strip()

        if json_str:
            try:
                json_obj = json.loads(json_str)
                return json_obj
            except json.JSONDecodeError as error:
                logger.error(
                    f"Streamlit Extracted string is not valid JSON. Returning raw string. Error: {error}"
                )
                return content_str

        return content_str

    def __unescape_dict(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self.__unescape_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.__unescape_dict(item) for item in data]
        elif isinstance(data, str):
            return data
        else:
            return data
