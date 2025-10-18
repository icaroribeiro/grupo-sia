import streamlit as st
import json
import pandas as pd
import altair as alt
from typing import Dict, Any, List

from dependency_injector.wiring import Provide, inject

from src.layers.business_layer.ai_agents.workflow_runner import WorkflowRunner
from src.layers.business_layer.ai_agents.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)
from src.layers.core_logic_layer.logging import logger
import plotly.express as px


class BaseDashboardTab:
    TAB_TITLE: str = "Base Tab"
    METRIC_COLUMN: str = "total_value_sum"
    METRIC_LABEL: str = "Valor Total (R$)"
    METRIC_TYPE: str = "currency"
    METRIC_TOOLTIP_FORMAT: str = "$,.2f"
    GROUP_BY_COLUMN: str = "uf_code"

    def __init__(self, parent_page: Any) -> None:
        self.streamlit_app_settings = parent_page.streamlit_app_settings

    def get_agent_format_instructions(self, question: str) -> Dict[str, Any]:
        group_by = self.GROUP_BY_COLUMN.replace("_code", "").replace("uf", "state")

        format_instructions = {
            "title": "brazil_invoice_data",
            "type": "object",
            "properties": {
                "data_by_group": {
                    "type": "array",
                    "description": f"List of data aggregated by Brazilian {group_by} for: {self.METRIC_LABEL}.",
                    "items": {
                        "type": "object",
                        "properties": {
                            self.GROUP_BY_COLUMN: {"type": "string"},
                            self.METRIC_COLUMN: {"type": "number"},
                        },
                        "required": [self.GROUP_BY_COLUMN, self.METRIC_COLUMN],
                    },
                }
            },
            "required": ["data_by_group"],
        }

        format_instructions_str = json.dumps(format_instructions, indent=2)

        input_message = f"""
        INSTRUCTIONS:
        - Perform a multi-step procedure to analyze data based on the user's question.
            1. Analyze the user's question accurately: {question}
            2. Format the final answer to the user's question as a JSON object that strictly adheres to the following schema:
            ```json
            {format_instructions_str}
            ```
        
        CRITICAL RULES:
        - **ALWAYS** return a JSON object, not a string of a JSON object.
        - DO NOT include any other text or explanations outside of the JSON object itself.
        """

        return {
            "input_message": input_message,
            "format_instructions_str": format_instructions_str,
        }

    def render(
        self,
        selected_year: int,
        selected_color_theme: str,
        df_multi_year: pd.DataFrame,
        geojson: Dict[str, Any],
        data_for_map: List[Dict[str, Any]],
    ):
        st.markdown(
            f"### Análise de {self.METRIC_LABEL} por {self.GROUP_BY_COLUMN.replace('_code', '').upper().replace('UF', 'UF EMITENTE').replace('OPERATION_NATURE', 'NATUREZA DA OPERAÇÃO').replace('BUYER_PRESENCE', 'MODALIDADE DE VENDA')} - Ano Fiscal {selected_year}"
        )

        df_map_data = pd.DataFrame(data_for_map)

        if not df_map_data.empty:
            df_map_data = df_map_data.sort_values(
                by=self.METRIC_COLUMN, ascending=False
            ).reset_index(drop=True)

            if self.GROUP_BY_COLUMN == "uf_code":
                df_map_data["geojson_id"] = df_map_data["uf_code"].apply(
                    self.__to_geojson_id
                )

        col_left, col_right = st.columns((5, 3), gap="large")

        with col_left:
            # ONLY render map and multi-year chart if grouping is by UF
            if self.GROUP_BY_COLUMN == "uf_code":
                map_fig = self.__make_choropleth(
                    df_map_data, geojson, selected_color_theme
                )
                if map_fig:
                    st.plotly_chart(map_fig, use_container_width=True)

                st.markdown("---")

                df_bar_chart = df_multi_year.copy()
                required_cols = ["uf_code", "year", self.METRIC_COLUMN]

                if all(col in df_bar_chart.columns for col in required_cols):
                    df_bar_chart = df_bar_chart[required_cols]
                    df_bar_chart.dropna(subset=[self.METRIC_COLUMN], inplace=True)
                else:
                    df_bar_chart = pd.DataFrame()

                if df_bar_chart.empty:
                    st.warning(
                        f"Não há dados multi-anuais para o gráfico de barras de {self.METRIC_LABEL}."
                    )
                else:
                    bar_chart = self.__make_bar_chart_by_year_and_uf(
                        df_bar_chart, selected_color_theme
                    )
                    if bar_chart:
                        st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.info(
                    f"Gráfico principal de Distribuição/Série Temporal não aplicável ou disponível para o agrupamento '{self.TAB_TITLE}'. Consulte as métricas e a tabela ao lado."
                )

        with col_right:
            self.__render_summary_metrics(df_map_data)

            st.markdown("---")

            self.__render_data_table(df_map_data)

        if not df_map_data.empty and self.GROUP_BY_COLUMN == "uf_code":
            with st.expander(f"Ver Dados Brutos Utilizados ({self.METRIC_LABEL})"):
                df_display = df_map_data.copy()
                if "uf_code" in df_display.columns:
                    df_display["state_name"] = df_display["uf_code"].apply(
                        self.streamlit_app_settings.get_state_name_by_uf_code
                    )
                    df_display = df_display.rename(
                        columns={
                            "uf_code": "UF",
                            "state_name": "Nome do Estado",
                            self.METRIC_COLUMN: self.METRIC_LABEL,
                            "geojson_id": "GeoJSON ID",
                        }
                    )
                    column_order = [
                        "UF",
                        "Nome do Estado",
                        self.METRIC_LABEL,
                        "GeoJSON ID",
                    ]
                else:
                    df_display = df_display.rename(
                        columns={
                            self.METRIC_COLUMN: self.METRIC_LABEL,
                            self.GROUP_BY_COLUMN: self.GROUP_BY_COLUMN.replace(
                                "_", " "
                            ).title(),
                        }
                    )
                    column_order = list(df_display.columns)

                st.dataframe(df_display[column_order], use_container_width=True)

    @staticmethod
    def __format_number(num, metric_type="currency"):
        if pd.isna(num) or num is None:
            return "R$ 0" if metric_type in ["currency", "average"] else "0"

        if metric_type == "count":
            # Format as integer with dot as thousands separator (Portuguese/Brazilian standard)
            return f"{int(num):,}".replace(",", "TEMP_MARKER").replace(
                "TEMP_MARKER", "."
            )

        magnitude = 0
        original_num = float(num)  # Ensure float for consistent calculation
        num_to_scale = abs(original_num)

        # Scale calculation for K, M, B, T
        while num_to_scale >= 1000 and magnitude < 4:
            magnitude += 1
            num_to_scale /= 1000.0

        if magnitude == 0:
            formatted_str = f"{original_num:,.2f}"
            suffix = ""
        else:
            formatted_str = f"{num_to_scale:.1f}"
            suffix = ["", " K", " M", " B", " T"][magnitude]

        # Handle sign correctly, especially for scaled numbers
        sign = "-" if original_num < 0 else ""

        # Currency symbol and formatting using Brazilian standards (comma for decimal, dot for thousands)
        # The initial Python f-string formatting f"{num_to_scale:.1f}" uses a dot for decimal on many systems.
        # We apply a manual swap to ensure Brazilian standard: comma as decimal separator.

        # 1. Start with the raw formatted number string
        raw_number_part = formatted_str.replace(".", "TEMP_DECIMAL_MARKER").replace(
            ",", "TEMP_THOUSANDS_MARKER"
        )

        # 2. Swap placeholders: dot becomes thousands separator (.), comma becomes decimal (,)
        final_number_part = raw_number_part.replace("TEMP_DECIMAL_MARKER", ",").replace(
            "TEMP_THOUSANDS_MARKER", "."
        )

        final_output = f"R$ {final_number_part}{suffix}"

        # Fix the issue where R$ . appears for very small numbers formatted as R$ 0,xx
        final_output = final_output.replace("R$ .", "R$ 0,")

        # Add sign back
        if sign == "-" and final_output.startswith("R$ "):
            final_output = final_output.replace("R$ ", "R$ -")

        return final_output.replace(
            "R$ -", f"-{final_output.split('R$ ')[-1]}"
        )  # Ensure negative sign is outside R$ if needed

    @staticmethod
    def __to_geojson_id(uf_code: str) -> str:
        return "BR" + uf_code.strip() if isinstance(uf_code, str) else None

    def __make_choropleth(self, df: pd.DataFrame, geojson: dict, color_theme: str):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        if df.empty or geojson is None:
            st.warning(
                f"Não há dados de UF ou GeoJSON disponível para plotagem do mapa de {label}."
            )
            return None

        max_value = df[metric].max() if not df.empty else 0

        st.markdown(f"##### **Mapa de {label} por UF Emitente**")  # Bolded title

        fig = px.choropleth(
            df,
            geojson=geojson,
            locations="geojson_id",
            featureidkey="properties.id",
            color=metric,
            color_continuous_scale=color_theme,
            range_color=(0, max_value * 1.05),
            scope="south america",
            center={"lat": -14, "lon": -50},
            labels={metric: label},
            height=600,
            hover_name="uf_code",
        )

        fig.update_geos(
            fitbounds="geojson",
            visible=False,
            projection_scale=1,
            center=dict(lat=-14, lon=-50),
            showland=True,
            landcolor="lightgray",
        )
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0}, coloraxis_colorbar_title_text=label
        )
        return fig

    def __make_bar_chart_by_year_and_uf(self, df: pd.DataFrame, color_theme: str):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        if df.empty:
            return None

        st.markdown(f"#### {label} por UF ao Longo dos Anos")

        df["year"] = df["year"].astype(str)
        max_value_for_color = df[metric].max()

        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(
                    "uf_code:N", axis=alt.Axis(title="Estado (UF)", labelAngle=-45)
                ),
                y=alt.Y("year:O", axis=alt.Axis(title="Ano")),
                color=alt.Color(
                    f"{metric}:Q",
                    title=label,
                    scale=alt.Scale(
                        scheme=color_theme.lower(),
                        domain=[0, max_value_for_color * 1.05],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("year:O", title="Ano"),
                    alt.Tooltip("uf_code:N", title="Estado"),
                    alt.Tooltip(
                        f"{metric}:Q", title=label, format=self.METRIC_TOOLTIP_FORMAT
                    ),
                ],
            )
            .properties(title="Comparativo Multi-Anual", height=300)
            .interactive()
        )

        return chart

    def __render_summary_metrics(self, df_map_data: pd.DataFrame):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL
        metric_type = self.METRIC_TYPE

        group_col_label = (
            "UF Emitente"
            if self.GROUP_BY_COLUMN == "uf_code"
            else (
                "Natureza da Operação"
                if self.GROUP_BY_COLUMN == "operation_nature"
                else "Modalidade de Venda"
            )
        )

        st.markdown(f"##### Top/Bottom {label} por {group_col_label}")

        if not df_map_data.empty and not df_map_data[metric].isnull().all():
            df_map_data = df_map_data.sort_values(
                by=metric, ascending=False
            ).reset_index(drop=True)

            if len(df_map_data) >= 1 and not pd.isna(df_map_data[metric].iloc[0]):
                top_group_name = df_map_data[self.GROUP_BY_COLUMN].iloc[0]
                top_group_value = self.__format_number(
                    df_map_data[metric].iloc[0], metric_type
                )
            else:
                top_group_name = "N/A"
                top_group_value = self.__format_number(None, metric_type)

            if len(df_map_data) >= 1 and not pd.isna(df_map_data[metric].iloc[-1]):
                bottom_group_name = df_map_data[self.GROUP_BY_COLUMN].iloc[-1]
                bottom_group_value = self.__format_number(
                    df_map_data[metric].iloc[-1], metric_type
                )
            else:
                bottom_group_name = "N/A"
                bottom_group_value = self.__format_number(None, metric_type)

            total_value = self.__format_number(df_map_data[metric].sum(), metric_type)
            unique_groups_count = df_map_data[self.GROUP_BY_COLUMN].nunique()

            # --- New layout for 2x2 metrics: two items above, two items below ---
            col_top_1, col_top_2 = st.columns(2)

            # Split the group name for better display if it contains a separator (like '9 - OPERAÇÃO...')
            top_display_name = top_group_name.split(" - ")[-1].strip()
            bottom_display_name = bottom_group_name.split(" - ")[-1].strip()

            with col_top_1:
                st.metric(
                    label=f"🥇 Maior {label} ({top_display_name})",
                    value=top_group_value,
                )
            with col_top_2:
                st.metric(
                    label=f"👎 Menor {label} ({bottom_display_name})",
                    value=bottom_group_value,
                )

            # Separator for visual grouping
            st.markdown("---")

            col_bottom_1, col_bottom_2 = st.columns(2)
            with col_bottom_1:
                st.metric(label=f"📑 Total Geral ({label})", value=total_value)
            with col_bottom_2:
                st.metric(
                    label=f"🗃️ {group_col_label}s únicos", value=unique_groups_count
                )
            # ----------------------------------------------------------------------

        else:
            st.info("Dados insuficientes para calcular métricas de Top/Bottom.")

    def __render_data_table(self, df_map_data: pd.DataFrame):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        group_col_label = (
            "UF"
            if self.GROUP_BY_COLUMN == "uf_code"
            else (
                "Operação"
                if self.GROUP_BY_COLUMN == "operation_nature"
                else "Modalidade"
            )
        )
        # Title for the table (corrected spacing)
        st.markdown(f"##### **Top Grupos por {label}**")

        if not df_map_data.empty:
            # Check for non-null/non-NaN values for max_val calculation
            valid_metric_values = df_map_data[metric].dropna()
            if not valid_metric_values.empty:
                max_val = float(valid_metric_values.max())
            else:
                max_val = 0.0  # Set to 0 if all are null/NaN to prevent error

            if self.METRIC_TYPE in ["currency", "average"]:
                progress_format = "R$ %.2f"
            elif self.METRIC_TYPE == "count":
                progress_format = "%.0f"
            else:
                progress_format = "%.2f"

            st.dataframe(
                df_map_data.rename(
                    columns={self.GROUP_BY_COLUMN: group_col_label, metric: label}
                ),
                column_order=(group_col_label, label),
                hide_index=True,
                column_config={
                    group_col_label: st.column_config.TextColumn(group_col_label),
                    label: st.column_config.ProgressColumn(
                        label,
                        format=progress_format,
                        min_value=0.0,
                        max_value=max_val,
                    ),
                },
                height=450,  # Added height for extended size perception
            )
        else:
            st.info("Nenhum dado disponível para o ano selecionado.")


class TotalValueTab(BaseDashboardTab):
    TAB_TITLE = "Faturamento Total (R$)"
    METRIC_COLUMN = "total_value_sum"
    METRIC_LABEL = "Valor Total (R$)"
    METRIC_TYPE = "currency"
    METRIC_TOOLTIP_FORMAT = "$,.2f"


class InvoiceCountTab(BaseDashboardTab):
    TAB_TITLE = "Contagem de NF-e"
    METRIC_COLUMN = "num_invoices"
    METRIC_LABEL = "Número de NF-e"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","


class AverageValueTab(BaseDashboardTab):
    TAB_TITLE = "Valor Médio NF-e (R$)"
    METRIC_COLUMN = "avg_invoice_value"
    METRIC_LABEL = "Valor Médio da NF-e (R$)"
    METRIC_TYPE = "average"
    METRIC_TOOLTIP_FORMAT = "$,.2f"


class OperationNatureTab(BaseDashboardTab):
    TAB_TITLE = "Natureza da Operação"
    METRIC_COLUMN = "operation_count"
    METRIC_LABEL = "Contagem por Operação"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "operation_nature"


class BuyerPresenceTab(BaseDashboardTab):
    TAB_TITLE = "Modalidade de Venda"
    METRIC_COLUMN = "presence_count"
    METRIC_LABEL = "Contagem por Modalidade"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "buyer_presence"


class DataAnalysisPage:
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
        self.streamlit_app_settings = streamlit_app_settings
        self.invoice_mgmt_workflow = invoice_mgmt_workflow
        self.workflow_runner = workflow_runner
        self.tabs = {
            TotalValueTab.TAB_TITLE: TotalValueTab(self),
            AverageValueTab.TAB_TITLE: AverageValueTab(self),
            InvoiceCountTab.TAB_TITLE: InvoiceCountTab(self),
            OperationNatureTab.TAB_TITLE: OperationNatureTab(self),
            BuyerPresenceTab.TAB_TITLE: BuyerPresenceTab(self),
        }

    def show(self) -> None:
        st.title("📊 Análise de Dados")
        geojson = self.__load_brazil_geojson()

        with st.sidebar:
            st.title("⚙️ Filtros de Dashboard")
            selected_year = st.selectbox("Selecione o Ano Fiscal", YEAR_LIST, index=0)
            selected_color_theme = st.selectbox(
                "Selecione um Esquema de Cores", COLOR_THEME_LIST, index=0
            )

        tab_titles = list(self.tabs.keys())
        st_tabs = st.tabs(tab_titles)

        with st.spinner(
            f"🚀 Analisando dados de {selected_year} com o Agente de IA..."
        ):
            try:
                data = self.__run_dummy_data_simulation(selected_year)
                df_multi_year = pd.DataFrame(data["multi_year_data"])
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                st.error(f"Falha na execução do workflow de análise: {e}")
                data = {
                    "uf_data": [],
                    "operation_data": [],
                    "presence_data": [],
                    "multi_year_data": [],
                }
                df_multi_year = pd.DataFrame()

        for tab_title, st_tab in zip(tab_titles, st_tabs):
            with st_tab:
                tab_instance = self.tabs[tab_title]

                if tab_instance.GROUP_BY_COLUMN == "uf_code":
                    question_template = f"Calculate the {tab_instance.METRIC_LABEL} ({tab_instance.METRIC_COLUMN}) grouped by emitter_uf for the year {selected_year}."
                    data_source_key = "uf_data"
                elif tab_instance.GROUP_BY_COLUMN == "operation_nature":
                    question_template = f"Calculate the count of invoices grouped by operation_nature for the year {selected_year}."
                    data_source_key = "operation_data"
                else:
                    question_template = f"Calculate the count of invoices grouped by buyer_presence for the year {selected_year}."
                    data_source_key = "presence_data"

                source_data = data.get(data_source_key, [])

                if st.checkbox(
                    f"Mostrar Instruções do Agente ({tab_title})", value=False
                ):
                    agent_info = tab_instance.get_agent_format_instructions(
                        question_template
                    )
                    st.code(agent_info["input_message"], language="markdown")
                    st.code(agent_info["format_instructions_str"], language="json")

                data_for_map = [
                    {
                        tab_instance.GROUP_BY_COLUMN: d[tab_instance.GROUP_BY_COLUMN],
                        tab_instance.METRIC_COLUMN: d.get(tab_instance.METRIC_COLUMN),
                    }
                    for d in source_data
                    if tab_instance.METRIC_COLUMN in d
                ]

                tab_instance.render(
                    selected_year,
                    selected_color_theme,
                    df_multi_year,
                    geojson,
                    data_for_map,
                )

    def __load_brazil_geojson(self) -> Any:
        geojson_path = (
            f"{self.streamlit_app_settings.assets_dir_path}/brazilian_states.json"
        )
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"GeoJSON file not found at: {geojson_path}")
            st.error(
                f"Erro: Arquivo GeoJSON de fronteiras estaduais ({geojson_path}) não encontrado."
            )
            return None
        except Exception as e:
            logger.error(f"Error loading GeoJSON: {e}")
            st.error("Erro ao carregar o arquivo GeoJSON.")
            return None

    def __run_dummy_data_simulation(
        self, selected_year: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        if selected_year == 2025:
            uf_data = [
                {
                    "uf_code": "MG",
                    "total_value_sum": 8040.00,
                    "num_invoices": 150,
                    "avg_invoice_value": 53.60,
                },
                {
                    "uf_code": "GO",
                    "total_value_sum": 1368.50,
                    "num_invoices": 20,
                    "avg_invoice_value": 68.43,
                },
                {
                    "uf_code": "SC",
                    "total_value_sum": 11990.00,
                    "num_invoices": 80,
                    "avg_invoice_value": 149.88,
                },
                {
                    "uf_code": "RJ",
                    "total_value_sum": 5000.00,
                    "num_invoices": 30,
                    "avg_invoice_value": 166.67,
                },
                {
                    "uf_code": "SP",
                    "total_value_sum": 15000.00,
                    "num_invoices": 250,
                    "avg_invoice_value": 60.00,
                },
            ]
            operation_data = [
                {"operation_nature": "Outra saida merc.", "operation_count": 150},
                {
                    "operation_nature": "VENDA DE MERCADORIA ADQUIRIDA OU RECEBIDA DE TERCEIROS",
                    "operation_count": 20,
                },
                {"operation_nature": "VENDA-DE PRODUCAO RURAL", "operation_count": 80},
                {"operation_nature": "REMESSA P/ CONSERTO", "operation_count": 280},
            ]
            presence_data = [
                {
                    "buyer_presence": "9 - OPERAÇÃO NÃO PRESENCIAL, OUTROS",
                    "presence_count": 300,
                },
                {"buyer_presence": "1 - OPERAÇÃO PRESENCIAL", "presence_count": 100},
                {
                    "buyer_presence": "2 - OPERAÇÃO NÃO PRESENCIAL, INTERNET",
                    "presence_count": 130,
                },
            ]
        elif selected_year == 2024:
            uf_data = [
                {
                    "uf_code": "SP",
                    "total_value_sum": 550000.00,
                    "num_invoices": 1200,
                    "avg_invoice_value": 458.33,
                },
                {
                    "uf_code": "BA",
                    "total_value_sum": 200000.00,
                    "num_invoices": 500,
                    "avg_invoice_value": 400.00,
                },
                {
                    "uf_code": "MG",
                    "total_value_sum": 30000.00,
                    "num_invoices": 100,
                    "avg_invoice_value": 300.00,
                },
                {
                    "uf_code": "DF",
                    "total_value_sum": 10000.00,
                    "num_invoices": 50,
                    "avg_invoice_value": 200.00,
                },
            ]
            operation_data = [
                {"operation_nature": "Outra saida merc.", "operation_count": 600},
                {
                    "operation_nature": "VENDA DE MERCADORIA ADQUIRIDA OU RECEBIDA DE TERCEIROS",
                    "operation_count": 500,
                },
                {"operation_nature": "REMESSA P/ CONSERTO", "operation_count": 250},
            ]
            presence_data = [
                {
                    "buyer_presence": "9 - OPERAÇÃO NÃO PRESENCIAL, OUTROS",
                    "presence_count": 1200,
                },
                {"buyer_presence": "1 - OPERAÇÃO PRESENCIAL", "presence_count": 600},
            ]
        else:
            uf_data = [
                {
                    "uf_code": "SP",
                    "total_value_sum": 10000.00,
                    "num_invoices": 150,
                    "avg_invoice_value": 66.67,
                },
                {
                    "uf_code": "RJ",
                    "total_value_sum": 5000.00,
                    "num_invoices": 75,
                    "avg_invoice_value": 66.67,
                },
                {
                    "uf_code": "CE",
                    "total_value_sum": 8000.00,
                    "num_invoices": 100,
                    "avg_invoice_value": 80.00,
                },
            ]
            operation_data = [
                {"operation_nature": "Outra saida merc.", "operation_count": 150},
                {"operation_nature": "VENDA-DE PRODUCAO RURAL", "operation_count": 100},
                {"operation_nature": "REMESSA P/ CONSERTO", "operation_count": 75},
            ]

            presence_data = [
                {
                    "buyer_presence": "9 - OPERAÇÃO NÃO PRESENCIAL, OUTROS",
                    "presence_count": 180,
                },
                {"buyer_presence": "1 - OPERAÇÃO PRESENCIAL", "presence_count": 145},
            ]

        dummy_multi_year_data = [
            {
                "uf_code": "MG",
                "year": 2025,
                "total_value_sum": 8040.00,
                "num_invoices": 150,
                "avg_invoice_value": 53.60,
            },
            {
                "uf_code": "GO",
                "year": 2025,
                "total_value_sum": 1368.50,
                "num_invoices": 20,
                "avg_invoice_value": 68.43,
            },
            {
                "uf_code": "SC",
                "year": 2025,
                "total_value_sum": 11990.00,
                "num_invoices": 80,
                "avg_invoice_value": 149.88,
            },
            {
                "uf_code": "SP",
                "year": 2024,
                "total_value_sum": 550000.00,
                "num_invoices": 1200,
                "avg_invoice_value": 458.33,
            },
            {
                "uf_code": "BA",
                "year": 2024,
                "total_value_sum": 200000.00,
                "num_invoices": 500,
                "avg_invoice_value": 400.00,
            },
            {
                "uf_code": "MG",
                "year": 2024,
                "total_value_sum": 30000.00,
                "num_invoices": 100,
                "avg_invoice_value": 300.00,
            },
            {
                "uf_code": "SP",
                "year": 2023,
                "total_value_sum": 10000.00,
                "num_invoices": 150,
                "avg_invoice_value": 66.67,
            },
            {
                "uf_code": "CE",
                "year": 2023,
                "total_value_sum": 8000.00,
                "num_invoices": 100,
                "avg_invoice_value": 80.00,
            },
            {
                "uf_code": "MG",
                "year": 2022,
                "total_value_sum": 12000.00,
                "num_invoices": 80,
                "avg_invoice_value": 150.00,
            },
        ]

        return {
            "uf_data": uf_data,
            "operation_data": operation_data,
            "presence_data": presence_data,
            "multi_year_data": dummy_multi_year_data,
        }
