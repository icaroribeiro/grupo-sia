import asyncio
import json
import re
from typing import Any, Dict, List

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st
from dependency_injector.wiring import Provide, inject

from src.ai.workflow_runner import WorkflowRunner
from src.ai.workflows.invoice_mgmt_workflow import (
    InvoiceMgmtWorkflow,
)
from src.core.container.container import Container
from src.core.logging import logger
from src.settings.streamlit_app_settings import (
    StreamlitAppSettings,
)


class BaseDashboardTab:
    TAB_ID: str = "BASE"
    TAB_TITLE: str = "Base Tab"
    METRIC_COLUMN: str = "total_value_sum"
    METRIC_LABEL: str = "Valor Total (R$)"
    METRIC_TYPE: str = "currency"
    METRIC_TOOLTIP_FORMAT: str = "$,.2f"
    GROUP_BY_COLUMN: str = "emitter_uf"
    DISPLAY_TYPE = "map"

    def __init__(self, parent_page: Any) -> None:
        self.streamlit_app_settings = parent_page.streamlit_app_settings

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        group_by = self.GROUP_BY_COLUMN.replace("_code", "").replace("uf", "state")

        map_schema = {
            "type": "array",
            "description": f"List of data aggregated by Brazilian {group_by} for the selected year ({year}). Metric: {self.METRIC_LABEL}.",
            "items": {
                "type": "object",
                "properties": {
                    self.GROUP_BY_COLUMN: {
                        "type": "string",
                        "description": "The grouping column, e.g., 'AC', 'RJ', 'SP' or 'product_name'.",
                    },
                    self.METRIC_COLUMN: {
                        "type": "number",
                        "description": f"The calculated metric value: {self.METRIC_LABEL}.",
                    },
                },
                "required": [self.GROUP_BY_COLUMN, self.METRIC_COLUMN],
            },
        }

        multi_year_schema = {
            "type": "array",
            "description": f"List of data aggregated by year and {group_by} for all available years. Metric: {self.METRIC_LABEL}.",
            "items": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "The fiscal year."},
                    self.GROUP_BY_COLUMN: {
                        "type": "string",
                        "description": "The grouping column, e.g., 'AC', 'RJ', 'SP' or 'product_name'.",
                    },
                    self.METRIC_COLUMN: {
                        "type": "number",
                        "description": f"The calculated metric value: {self.METRIC_LABEL}.",
                    },
                },
                "required": ["year", self.GROUP_BY_COLUMN, self.METRIC_COLUMN],
            },
        }

        format_instructions = {
            "title": f"dashboard_data_{self.TAB_ID.lower()}",
            "type": "object",
            "properties": {
                "data_by_group": map_schema,
                "multi_year_data": multi_year_schema,
            },
            "required": ["data_by_group", "multi_year_data"],
        }
        format_instructions_str = json.dumps(format_instructions, indent=2)

        data_payload_for_agent = {
            "data_by_group": map_schema,
            "multi_year_data": multi_year_schema,
        }
        data_payload_str = json.dumps(data_payload_for_agent, indent=2)

        input_message = f"""
        INSTRUCTIONS:
        - Perform a multi-step procedure to analyze data based on the user's question.
            1. Analyze the user's question accurately: {question}
            2. Format the final answer to the user's question as a JSON object that strictly adheres to the schema for the **properties** key:
            ```json
            {data_payload_str}
            ```
        
        CRITICAL RULES:
        - **ALL** data is available in the database for analysis.
        - **ALWAYS** return a JSON object with ONLY the keys 'data_by_group' and 'multi_year_data' at the top level.
        - DO NOT include 'title', 'type', or 'properties' in the final returned JSON.
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
        st.markdown(f"### Análise de {self.METRIC_LABEL} - Ano Fiscal {selected_year}")
        st.markdown(f"Por: {self.GROUP_BY_COLUMN.replace('_code', '').upper()}")

        df_map_data = pd.DataFrame(data_for_map)

        if not df_map_data.empty:
            df_map_data = df_map_data.sort_values(
                by=self.METRIC_COLUMN, ascending=False
            ).reset_index(drop=True)

            if self.DISPLAY_TYPE == "map":
                df_map_data["geojson_id"] = df_map_data["emitter_uf"].apply(
                    self.__to_geojson_id
                )

        col_left, col_right = st.columns((5, 3), gap="large")

        with col_left:
            if self.DISPLAY_TYPE == "map":
                map_fig = self.__make_choropleth(
                    df_map_data, geojson, selected_color_theme
                )
                if map_fig:
                    st.plotly_chart(map_fig, use_container_width=True)

                st.markdown("---")

                self.__render_multi_year_table(df_multi_year, selected_color_theme)

            else:
                st.markdown(
                    f"##### Distribuição de {self.METRIC_LABEL} por {self.get_group_label()} - Ano Fiscal {selected_year}"
                )
                self.__render_data_table_main(df_map_data)

        with col_right:
            self.__render_summary_metrics(df_map_data)

            st.markdown("---")

            if self.GROUP_BY_COLUMN == "emitter_uf":
                self.__render_data_table(df_map_data)

        if not df_map_data.empty and self.GROUP_BY_COLUMN == "emitter_uf":
            with st.expander(f"Ver Dados Brutos Utilizados para {self.METRIC_LABEL}"):
                st.markdown(
                    f"##### Dados Anuais Brutos por UF Emitente ({selected_year})"
                )

                df_display = df_map_data.copy()
                if "emitter_uf" in df_display.columns:
                    df_display["state_name"] = df_display["emitter_uf"].apply(
                        self.streamlit_app_settings.get_state_name_by_emitter_uf
                    )
                    df_display = df_display.rename(
                        columns={
                            "emitter_uf": "UF",
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

                if not df_multi_year.empty:
                    st.markdown("##### Dados Multi-Anuais Brutos")

                    df_multi_year_display = df_multi_year.copy()

                    column_mapping = {
                        "year": "Ano",
                        self.GROUP_BY_COLUMN: self.get_group_label(),
                        self.METRIC_COLUMN: self.METRIC_LABEL,
                    }

                    df_multi_year_display = df_multi_year_display.rename(
                        columns=column_mapping
                    )

                    multi_year_column_order = [
                        "Ano",
                        self.get_group_label(),
                        self.METRIC_LABEL,
                    ]

                    final_cols = [
                        col
                        for col in multi_year_column_order
                        if col in df_multi_year_display.columns
                    ]

                    st.dataframe(
                        df_multi_year_display[final_cols], use_container_width=True
                    )

    @staticmethod
    def __format_number(num, metric_type="currency"):
        if pd.isna(num) or num is None:
            return "R$ 0" if metric_type in ["currency", "average"] else "0"

        if metric_type == "count":
            return f"{int(num):,}".replace(",", "TEMP_MARKER").replace(
                "TEMP_MARKER", "."
            )

        magnitude = 0
        original_num = float(num)
        num_to_scale = abs(original_num)

        while num_to_scale >= 1000 and magnitude < 4:
            magnitude += 1
            num_to_scale /= 1000.0

        if magnitude == 0:
            formatted_str = f"{original_num:,.2f}"
            suffix = ""
        else:
            formatted_str = f"{num_to_scale:.1f}"
            suffix = ["", " K", " M", " B", " T"][magnitude]

        sign = "-" if original_num < 0 else ""

        raw_number_part = formatted_str.replace(".", "TEMP_DECIMAL_MARKER").replace(
            ",", "TEMP_THOUSANDS_MARKER"
        )

        final_number_part = raw_number_part.replace("TEMP_DECIMAL_MARKER", ",").replace(
            "TEMP_THOUSANDS_MARKER", "."
        )

        final_output = f"R$ {final_number_part}{suffix}"

        final_output = final_output.replace("R$ .", "R$ 0,")

        if sign == "-" and final_output.startswith("R$ "):
            final_output = final_output.replace("R$ ", "R$ -")

        return final_output.replace("R$ -", f"-{final_output.split('R$ ')[-1]}")

    @staticmethod
    def __to_geojson_id(emitter_uf: str) -> str:
        # FIX: Ensure GeoJSON ID matches the format without hyphens (e.g., BRGO, BRMG)
        return "BR" + emitter_uf.strip() if isinstance(emitter_uf, str) else None

    def __make_choropleth(self, df: pd.DataFrame, geojson: dict, color_theme: str):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        if df.empty or geojson is None:
            st.warning(
                f"Não há dados de UF ou GeoJSON disponível para plotagem do mapa de {label}."
            )
            return None

        max_value = df[metric].max() if not df.empty else 0

        st.markdown(f"##### **Mapa de {label} por UF Emitente**")

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
            hover_name="emitter_uf",
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
                    "emitter_uf:N", axis=alt.Axis(title="Estado (UF)", labelAngle=-45)
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
                    alt.Tooltip("emitter_uf:N", title="Estado"),
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

        group_col_label = self.get_group_label()

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

            col_top_1, col_top_2 = st.columns(2)

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

            st.markdown("---")

            col_bottom_1, col_bottom_2 = st.columns(2)
            with col_bottom_1:
                st.metric(label=f"📑 Total Geral ({label})", value=total_value)
            with col_bottom_2:
                st.metric(
                    label=f"🗃️ {group_col_label}s únicos", value=unique_groups_count
                )

        else:
            st.info("Dados insuficientes para calcular métricas de Top/Bottom.")

    def get_group_label(self) -> str:
        MAPPING = {
            "emitter_uf": "UF Emitente",
            "ncm_sh_code": "NCM/SH",
            "product_service_description": "Produto/Serviço",
            "operation_nature": "Operação",
            "shipping_modality": "Modalidade",
            "buyer_presence": "Modalidade",
        }

        if self.GROUP_BY_COLUMN in MAPPING:
            return MAPPING[self.GROUP_BY_COLUMN]

        return self.GROUP_BY_COLUMN.replace("_", " ").title()

    def __render_data_table_main(self, df_map_data: pd.DataFrame):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL
        group_col_label = self.get_group_label()

        if not df_map_data.empty:
            valid_metric_values = df_map_data[metric].dropna()
            if not valid_metric_values.empty:
                max_val = float(valid_metric_values.max())
            else:
                max_val = 0.0

            if self.METRIC_TYPE in ["currency", "average"]:
                progress_format = "R$ %.2f"
            elif self.METRIC_TYPE == "count":
                progress_format = "%.0f"
            else:
                progress_format = "%.2f"

            df_table = df_map_data[[self.GROUP_BY_COLUMN, self.METRIC_COLUMN]].rename(
                columns={self.GROUP_BY_COLUMN: group_col_label, metric: label}
            )

            st.dataframe(
                df_table,
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
                height=650,
            )
        else:
            st.info("Nenhum dado disponível para o ano selecionado.")

    def __render_data_table(self, df_map_data: pd.DataFrame):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        group_col_label = self.get_group_label()

        st.markdown(f"##### **Top Grupos por {label}**")

        if not df_map_data.empty:
            valid_metric_values = df_map_data[metric].dropna()
            if not valid_metric_values.empty:
                max_val = float(valid_metric_values.max())
            else:
                max_val = 0.0

            if self.METRIC_TYPE in ["currency", "average"]:
                progress_format = "R$ %.2f"
            elif self.METRIC_TYPE == "count":
                progress_format = "%.0f"
            else:
                progress_format = "%.2f"

            df_table = df_map_data[[self.GROUP_BY_COLUMN, self.METRIC_COLUMN]].rename(
                columns={self.GROUP_BY_COLUMN: group_col_label, metric: label}
            )

            st.dataframe(
                df_table,
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
                height=450,
            )
        else:
            st.info("Nenhum dado disponível para o ano selecionado.")

    def __render_multi_year_table(
        self, df_multi_year: pd.DataFrame, selected_color_theme: str
    ):
        metric = self.METRIC_COLUMN

        if df_multi_year.empty:
            st.warning("Não há dados multi-anuais para esta análise.")
            return

        df_bar_chart = df_multi_year.copy()
        required_cols = [self.GROUP_BY_COLUMN, "year", metric]

        if all(col in df_bar_chart.columns for col in required_cols):
            df_bar_chart = df_bar_chart[required_cols]
            df_bar_chart.dropna(subset=[metric], inplace=True)
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


class InvoiceCountTab(BaseDashboardTab):
    TAB_ID = "INVOICE_COUNT_UF"
    TAB_TITLE = "Contagem de NF-e"
    METRIC_COLUMN = "num_invoices"
    METRIC_LABEL = "Número de NF-e"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "emitter_uf"
    DISPLAY_TYPE = "map"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class InvoiceItemCountTab(BaseDashboardTab):
    TAB_ID = "INVOICE_ITEM_COUNT_UF"
    TAB_TITLE = "Contagem de Itens (Volume)"
    METRIC_COLUMN = "item_count"
    METRIC_LABEL = "Número de Itens (Linhas NF-e)"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "emitter_uf"
    DISPLAY_TYPE = "map"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class InvoiceItemQuantityTab(BaseDashboardTab):
    TAB_ID = "INVOICE_ITEM_QUANTITY_UF"
    TAB_TITLE = "Total de Quantidade"
    METRIC_COLUMN = "total_quantity"
    METRIC_LABEL = "Quantidade Total (Unidades/KG/etc.)"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "emitter_uf"
    DISPLAY_TYPE = "map"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class InvoiceItemByProductTab(BaseDashboardTab):
    TAB_ID = "INVOICE_ITEM_BY_PRODUCT"
    TAB_TITLE = "Top Produtos"
    METRIC_COLUMN = "item_total_value_sum"
    METRIC_LABEL = "Valor Total do Item (R$)"
    METRIC_TYPE = "currency"
    GROUP_BY_COLUMN = "product_service_description"
    DISPLAY_TYPE = "table"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class ProductCountTab(BaseDashboardTab):
    TAB_ID = "PRODUCT_COUNT"
    TAB_TITLE = "Produtos Mais Vendidos"
    METRIC_COLUMN = "product_count"
    METRIC_LABEL = "Contagem de Produtos"
    METRIC_TYPE = "count"
    GROUP_BY_COLUMN = "product_service_description"
    DISPLAY_TYPE = "table"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class InvoiceAverageValueTab(BaseDashboardTab):
    TAB_ID = "INVOICE_AVG_VALUE_UF"
    TAB_TITLE = "Valor Médio NF-e (R$)"
    METRIC_COLUMN = "avg_invoice_value"
    METRIC_LABEL = "Valor Médio da NF-e (R$)"
    METRIC_TYPE = "average"
    METRIC_TOOLTIP_FORMAT = "$,.2f"
    GROUP_BY_COLUMN = "emitter_uf"
    DISPLAY_TYPE = "map"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class InvoiceTotalValueTab(BaseDashboardTab):
    TAB_ID = "INVOICE_TOTAL_VALUE_UF"
    TAB_TITLE = "Faturamento Total (R$)"
    METRIC_COLUMN = "total_value_sum"
    METRIC_LABEL = "Valor Total (R$)"
    METRIC_TYPE = "currency"
    METRIC_TOOLTIP_FORMAT = "$,.2f"
    GROUP_BY_COLUMN = "emitter_uf"
    DISPLAY_TYPE = "map"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


class InvoiceItemTotalValueTab(BaseDashboardTab):
    TAB_ID = "INVOICE_ITEM_TOTAL_VALUE_UF"
    TAB_TITLE = "Faturamento por Item (R$)"
    METRIC_COLUMN = "item_total_value_sum"
    METRIC_LABEL = "Valor Total do Item (R$)"
    METRIC_TYPE = "currency"
    GROUP_BY_COLUMN = "emitter_uf"
    DISPLAY_TYPE = "map"

    def get_agent_format_instructions(self, question: str, year: int) -> Dict[str, Any]:
        return super().get_agent_format_instructions(question, year)


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
            InvoiceCountTab.TAB_TITLE: InvoiceCountTab(self),
            InvoiceItemCountTab.TAB_TITLE: InvoiceItemCountTab(self),
            InvoiceItemQuantityTab.TAB_TITLE: InvoiceItemQuantityTab(self),
            InvoiceItemByProductTab.TAB_TITLE: InvoiceItemByProductTab(self),
            ProductCountTab.TAB_TITLE: ProductCountTab(self),
            InvoiceAverageValueTab.TAB_TITLE: InvoiceAverageValueTab(self),
            InvoiceTotalValueTab.TAB_TITLE: InvoiceTotalValueTab(self),
            InvoiceItemTotalValueTab.TAB_TITLE: InvoiceItemTotalValueTab(self),
        }

        if "workflow_cache" not in st.session_state:
            st.session_state.workflow_cache = {}

    def show(self) -> None:
        st.title("📊 Análise de Dados")
        st.markdown(
            'Escolha uma das opções em **"Selecione a Análise"** para visualizar métricas'
            " detalhadas de faturamento (**Valor Total**), **Contagem de NF-e**, "
            "**Volume de Itens** e muito mais, organizadas por **UF Emitente** ou **Produto/Serviço**. "
            "Os dados são apresentados em mapas coropléticos, gráficos de tendência e tabelas interativas."
        )
        geojson = self.__load_brazil_geojson()

        if "workflow_cache" not in st.session_state:
            st.session_state.workflow_cache = {}

        tab_titles = list(self.tabs.keys())

        with st.sidebar:
            st.title("⚙️ Filtros de Dashboard")
            selected_year = st.selectbox(
                "Selecione o Ano Fiscal",
                self.streamlit_app_settings.get_year_list(),
                key="selected_year_filter",
            )
            selected_color_theme = st.selectbox(
                "Selecione um Esquema de Cores",
                self.streamlit_app_settings.get_color_theme_list(),
                index=0,
            )

        selected_tab_title = st.selectbox(
            "Selecione a Análise:",
            tab_titles,
            index=0,
            key="selected_analysis_selectbox",
        )

        tab_instance = self.tabs[selected_tab_title]

        cache_key = f"{tab_instance.TAB_ID}_{selected_year}"

        response = None
        agent_info = None

        if cache_key not in st.session_state.workflow_cache:
            with st.spinner(
                f"🚀 Analisando dados de {selected_tab_title} para o ano {selected_year}..."
            ):
                group_label = tab_instance.get_group_label()
                question_template = f"Calculate the {tab_instance.METRIC_LABEL} ({tab_instance.METRIC_COLUMN}) grouped by {group_label} ({tab_instance.GROUP_BY_COLUMN}) for the year {selected_year} and also for all years."

                agent_info = tab_instance.get_agent_format_instructions(
                    question_template, selected_year
                )
                input_message = agent_info["input_message"]

                response = asyncio.run(
                    self.workflow_runner.run_workflow(
                        self.invoice_mgmt_workflow,
                        input_message,
                        st.session_state.session_thread_id
                        if "session_thread_id" in st.session_state
                        else "dummy_thread_id",
                    )
                )

                st.session_state.workflow_cache[cache_key] = {
                    "response": response,
                    "agent_info": agent_info,
                }

        # --- Data Processing and Rendering ---
        cached_data = st.session_state.workflow_cache.get(cache_key)
        if not cached_data:
            st.error("Erro ao carregar ou executar o workflow.")
            return

        response = cached_data["response"]
        agent_info = cached_data["agent_info"]

        final_message = response["messages"][-1]
        final_response_str = final_message.content
        logger.info(f"final_response_str: {final_response_str}")
        response_data = self.__extract_json_from_content(final_response_str)
        logger.info(f"response_data: {response_data}")

        if not isinstance(response_data, dict):
            st.error(
                f"❌ Erro de Processamento: O agente não retornou os dados no formato esperado para **{selected_tab_title}**."
            )
            st.warning(
                "Pode haver um problema na comunicação com o modelo ou a estrutura do JSON está incompleta."
            )
            with st.expander("Ver Resposta Bruta do Agente"):
                st.code(final_response_str, language="markdown")
            return

        source_map_data = response_data.get("data_by_group", [])
        source_multi_year_data = response_data.get("multi_year_data", [])

        data_for_map = [
            {
                tab_instance.GROUP_BY_COLUMN: d.get(tab_instance.GROUP_BY_COLUMN),
                tab_instance.METRIC_COLUMN: d.get(tab_instance.METRIC_COLUMN),
            }
            for d in source_map_data
            if isinstance(d, dict)
        ]

        df_multi_year = pd.DataFrame(source_multi_year_data)

        if st.checkbox(
            f"Mostrar Instruções do Agente ({selected_tab_title})",
            value=False,
            key=f"agent_check_{tab_instance.TAB_ID}",
        ):
            st.code(agent_info["input_message"], language="markdown")
            st.code(agent_info["format_instructions_str"], language="json")

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

    @staticmethod
    def __extract_json_from_content(content_str: str) -> dict | str:
        json_match = re.search(r"(\{[\s\S]*\})", content_str)

        json_str = None
        if json_match:
            json_str = json_match.group(0).strip().strip("`").strip()
        else:
            json_pattern = r"content='(\{.*\})'"
            json_match_old = re.search(json_pattern, content_str, re.DOTALL)
            if json_match_old:
                json_str = json_match_old.group(1).strip()
            else:
                json_str = content_str.strip()

        if json_str:
            try:
                json_str = re.sub(r",\s*\}", "}", json_str)
                json_str = re.sub(r",\s*\]", "]", json_str)

                json_obj = json.loads(json_str)
                return json_obj
            except json.JSONDecodeError as error:
                logger.error(
                    f"Streamlit Extracted string is not valid JSON. Returning raw string. Error: {error}"
                )
                return content_str

        return content_str
