import streamlit as st
import json
import pandas as pd
import altair as alt
from typing import Dict, Any, List

# Reutilizando os imports de injeção de dependência e classes
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

# --- Configurações Comuns (Mantidas do seu código original) ---
YEAR_LIST = [2025, 2024, 2023, 2022]
COLOR_THEME_LIST = ["Viridis", "Plasma", "Inferno", "Cividis"]


def _format_number(num, metric_type="currency"):
    if pd.isna(num) or num is None:
        return "R$ 0" if metric_type in ["currency", "average"] else "0"

    if metric_type == "count":
        # Format as integer with dot as thousands separator (Portuguese/Brazilian standard)
        return f"{int(num):,}".replace(",", "TEMP_MARKER").replace("TEMP_MARKER", ".")

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


def _to_geojson_id(uf_code: str) -> str:
    return "BR" + uf_code.strip() if isinstance(uf_code, str) else None


# ----------------------------------------------------------------------
## 1. Classe Base para as Guias de Item (BaseItemDashboardTab)
# ----------------------------------------------------------------------


class BaseItemDashboardTab:
    # Ajustando colunas para dados de ITEM
    TAB_TITLE: str = "Base Item Tab"
    METRIC_COLUMN: str = "item_total_value_sum"
    METRIC_LABEL: str = "Valor Total do Item (R$)"
    METRIC_TYPE: str = "currency"
    METRIC_TOOLTIP_FORMAT: str = "$,.2f"
    GROUP_BY_COLUMN: str = "emitter_uf"  # Usando emitter_uf para o mapa

    def __init__(self, parent_page: Any):
        self.parent = parent_page
        self.streamlit_app_settings = parent_page.streamlit_app_settings
        self.logger = logger

    def _get_group_label(self):
        if self.GROUP_BY_COLUMN == "emitter_uf":
            return "UF Emitente"
        elif self.GROUP_BY_COLUMN == "ncm_sh_code":
            return "NCM/SH"
        else:
            return self.GROUP_BY_COLUMN.replace("_", " ").title()

    def get_agent_format_instructions(self, question: str) -> Dict[str, Any]:
        """Gera as instruções para o Agente de IA para esta guia."""
        group_by = self.GROUP_BY_COLUMN.replace("emitter_uf", "emitter_state").replace(
            "_", " "
        )

        format_instructions = {
            "title": "brazil_invoice_item_data",
            "type": "object",
            "properties": {
                "data_by_group": {
                    "type": "array",
                    "description": f"List of data aggregated by {group_by} for: {self.METRIC_LABEL}.",
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

        # Mantendo o formato longo de instrução do seu modelo
        input_message = f"""
        INSTRUCTIONS:
        - Perform a multi-step procedure to analyze data based on the user's question.
        - The procedure consists of the following tasks executed only by the team responsible for data analysis.
            1. Analyze the user's question accurately: {question}
            2. Format the final answer to the user's question as a JSON object that strictly adheres to the following schema:
            ```json
            {format_instructions_str}
            ```
        
        CRITICAL RULES:
        - A JSON object must always be returned, not a string of a JSON object.
        - DO NOT include any other text or explanations outside of the JSON object itself.
        """
        return {
            "input_message": input_message,
            "format_instructions_str": format_instructions_str,
        }

    def _make_choropleth(self, df: pd.DataFrame, geojson: dict, color_theme: str):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        max_value = df[metric].max() if not df.empty else 0

        st.markdown(f"🗺️ Mapa de {label} por UF Emitente")

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
            hover_name=self.GROUP_BY_COLUMN,  # Será 'emitter_uf'
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

    def _make_bar_chart_by_year_and_uf(self, df: pd.DataFrame, color_theme: str):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL

        if df.empty:
            return None

        st.markdown(f"### {label} por UF ao Longo dos Anos")

        df["year"] = df["year"].astype(str)
        max_value_for_color = df[metric].max()

        # Usando 'emitter_uf' ao invés de 'uf_code'
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

    def _render_summary_metrics(self, df_map_data: pd.DataFrame):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL
        metric_type = self.METRIC_TYPE

        group_col_label = self._get_group_label()

        st.markdown(f"📈 Top/Bottom {label} por {group_col_label}")

        if not df_map_data.empty and not df_map_data[metric].isnull().all():
            df_map_data = df_map_data.sort_values(
                by=metric, ascending=False
            ).reset_index(drop=True)

            # Ensure we have at least one valid row for Top and two for Bottom (for robustness, though df is not empty check should cover)
            if len(df_map_data) >= 1 and not pd.isna(df_map_data[metric].iloc[0]):
                top_group_name = df_map_data[self.GROUP_BY_COLUMN].iloc[0]
                top_group_value = _format_number(
                    df_map_data[metric].iloc[0], metric_type
                )
            else:
                top_group_name = "N/A"
                top_group_value = _format_number(None, metric_type)

            if len(df_map_data) >= 1 and not pd.isna(df_map_data[metric].iloc[-1]):
                bottom_group_name = df_map_data[self.GROUP_BY_COLUMN].iloc[-1]
                bottom_group_value = _format_number(
                    df_map_data[metric].iloc[-1], metric_type
                )
            else:
                bottom_group_name = "N/A"
                bottom_group_value = _format_number(None, metric_type)

            total_value = _format_number(df_map_data[metric].sum(), metric_type)
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

        else:
            st.info("Dados insuficientes para calcular métricas de Top/Bottom.")

    def _render_data_table(self, df_data: pd.DataFrame):
        metric = self.METRIC_COLUMN
        label = self.METRIC_LABEL
        group_col_label = self._get_group_label()

        st.markdown(f"📋 Top Grupos por {label}")

        if not df_data.empty:
            max_val = float(df_data[metric].max())

            if self.METRIC_TYPE in ["currency", "average"]:
                progress_format = "R$ %.2f"
            elif self.METRIC_TYPE == "count":
                progress_format = "%.0f"
            else:
                progress_format = "%.2f"

            st.dataframe(
                df_data.rename(
                    columns={self.GROUP_BY_COLUMN: group_col_label, metric: label}
                ).head(20),
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
            )
        else:
            st.info("Nenhum dado disponível para o ano selecionado.")

    def render(
        self,
        selected_year: int,
        selected_color_theme: str,
        df_multi_year: pd.DataFrame,
        geojson: Dict[str, Any],
        data_for_tab: List[Dict[str, Any]],
    ):
        st.markdown(
            f"### Análise de {self.METRIC_LABEL} por {self._get_group_label().upper()} - Ano Fiscal {selected_year}"
        )

        df_data = pd.DataFrame(data_for_tab)

        if not df_data.empty:
            df_data = df_data.sort_values(
                by=self.METRIC_COLUMN, ascending=False
            ).reset_index(drop=True)

            if self.GROUP_BY_COLUMN == "emitter_uf":
                df_data["geojson_id"] = df_data["emitter_uf"].apply(_to_geojson_id)

        col_left, col_right = st.columns((3, 5), gap="large")

        with col_right:
            if self.GROUP_BY_COLUMN == "emitter_uf":
                # Renderizar Mapa
                map_fig = self._make_choropleth(df_data, geojson, selected_color_theme)
                if map_fig:
                    st.plotly_chart(map_fig, use_container_width=True)

                st.markdown("---")

                # Renderizar Gráfico Multi-Anual
                df_bar_chart = df_multi_year.copy()
                required_cols = ["emitter_uf", "year", self.METRIC_COLUMN]
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
                    bar_chart = self._make_bar_chart_by_year_and_uf(
                        df_bar_chart, selected_color_theme
                    )
                    if bar_chart:
                        st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.info(
                    "O mapa e o gráfico multi-anual são exibidos apenas para métricas agrupadas por UF."
                )

        with col_left:
            self._render_summary_metrics(df_data)
            st.markdown("---")
            self._render_data_table(df_data)

        # --- SEÇÃO DE "VER DADOS BRUTOS" NO FINAL DA PÁGINA ---
        if not df_data.empty and self.GROUP_BY_COLUMN == "emitter_uf":
            with st.expander(f"Ver Dados Brutos Utilizados ({self.METRIC_LABEL})"):
                df_display = df_data.copy()
                # A função 'get_state_name_by_uf_code' precisa existir em StreamlitAppSettings
                # para que isso funcione.
                # Exemplo: df_display["state_name"] = df_display["emitter_uf"].apply(self.streamlit_app_settings.get_state_name_by_uf_code)

                df_display = df_display.rename(
                    columns={
                        "emitter_uf": "UF",
                        self.METRIC_COLUMN: self.METRIC_LABEL,
                        "geojson_id": "GeoJSON ID",
                    }
                )
                column_order = ["UF", self.METRIC_LABEL, "GeoJSON ID"]
                st.dataframe(df_display[column_order], use_container_width=True)


# ----------------------------------------------------------------------
## 2. Implementação das 5 Guias (Ajustadas para Item)
# ----------------------------------------------------------------------


class ItemTotalValueTab(BaseItemDashboardTab):
    TAB_TITLE = "Faturamento por Item (R$)"
    METRIC_COLUMN = "item_total_value_sum"
    METRIC_LABEL = "Valor Total do Item (R$)"
    METRIC_TYPE = "currency"
    GROUP_BY_COLUMN = "emitter_uf"


class ItemCountTab(BaseItemDashboardTab):
    TAB_TITLE = "Contagem de Itens (Volume)"
    METRIC_COLUMN = "item_count"
    METRIC_LABEL = "Número de Itens (Linhas NF-e)"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "emitter_uf"


class ItemQuantityTab(BaseItemDashboardTab):
    TAB_TITLE = "Total de Quantidade"
    METRIC_COLUMN = "total_quantity"
    METRIC_LABEL = "Quantidade Total (Unidades/KG/etc.)"
    METRIC_TYPE = "count"
    METRIC_TOOLTIP_FORMAT = ","
    GROUP_BY_COLUMN = "emitter_uf"


class ItemByNCMTab(BaseItemDashboardTab):
    TAB_TITLE = "Análise por NCM/SH"
    METRIC_COLUMN = "item_total_value_sum"
    METRIC_LABEL = "Valor Total do Item (R$)"
    METRIC_TYPE = "currency"
    GROUP_BY_COLUMN = "ncm_sh_code"  # Agrupamento não-UF


class ItemByProductTab(BaseItemDashboardTab):
    TAB_TITLE = "Top Produtos"
    METRIC_COLUMN = "item_total_value_sum"
    METRIC_LABEL = "Valor Total do Item (R$)"
    METRIC_TYPE = "currency"
    GROUP_BY_COLUMN = "product_service_description"  # Agrupamento não-UF


# ----------------------------------------------------------------------
## 3. Classe da Página Principal de Itens (InvoiceItemAnalysisPage)
# ----------------------------------------------------------------------


class InvoiceItemAnalysisPage:
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
            ItemTotalValueTab.TAB_TITLE: ItemTotalValueTab(self),
            ItemCountTab.TAB_TITLE: ItemCountTab(self),
            ItemQuantityTab.TAB_TITLE: ItemQuantityTab(self),
            ItemByNCMTab.TAB_TITLE: ItemByNCMTab(self),
            ItemByProductTab.TAB_TITLE: ItemByProductTab(self),
        }

    def _load_brazil_geojson(self):
        # Implementação de carregamento de GeoJSON (mantida)
        geojson_path = "assets/brazilian_states.json"
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

    def _run_dummy_data_simulation(
        self, selected_year: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Simulação de dados de item, retornando agregações por:
        - UF (para as 3 primeiras abas e multi-anual)
        - NCM (para a aba de NCM)
        - Produto (para a aba de Produto)
        """

        # Dados Brutos de Exemplo (para agregação)
        raw_data = [
            # 2025 Data
            {
                "year": 2025,
                "emitter_uf": "MG",
                "product_service_description": "TAURUS PISTOLA G2C",
                "ncm_sh_code": "93020000",
                "quantity": 2.0,
                "total_value": 8040.0,
            },
            {
                "year": 2025,
                "emitter_uf": "MG",
                "product_service_description": "TAURUS PISTOLA G2C",
                "ncm_sh_code": "93020000",
                "quantity": 1.0,
                "total_value": 4020.0,
            },
            {
                "year": 2025,
                "emitter_uf": "GO",
                "product_service_description": "BATATA INGLESA",
                "ncm_sh_code": "07101000",
                "quantity": 50.0,
                "total_value": 350.0,
            },
            {
                "year": 2025,
                "emitter_uf": "GO",
                "product_service_description": "QUEIJO MUSSARELA",
                "ncm_sh_code": "04061090",
                "quantity": 20.0,
                "total_value": 700.0,
            },
            {
                "year": 2025,
                "emitter_uf": "SP",
                "product_service_description": "CIMENTO CP II",
                "ncm_sh_code": "25232910",
                "quantity": 500.0,
                "total_value": 15000.0,
            },
            # 2024 Data
            {
                "year": 2024,
                "emitter_uf": "SP",
                "product_service_description": "CIMENTO CP II",
                "ncm_sh_code": "25232910",
                "quantity": 500.0,
                "total_value": 17500.0,
            },
            {
                "year": 2024,
                "emitter_uf": "BA",
                "product_service_description": "AREIA LAVADA",
                "ncm_sh_code": "25059000",
                "quantity": 1000.0,
                "total_value": 20000.0,
            },
            {
                "year": 2024,
                "emitter_uf": "MG",
                "product_service_description": "NOTEBOOK CORE I7",
                "ncm_sh_code": "84713012",
                "quantity": 10.0,
                "total_value": 30000.0,
            },
            # 2023 Data
            {
                "year": 2023,
                "emitter_uf": "MG",
                "product_service_description": "NOTEBOOK CORE I7",
                "ncm_sh_code": "84713012",
                "quantity": 5.0,
                "total_value": 15000.0,
            },
            {
                "year": 2023,
                "emitter_uf": "GO",
                "product_service_description": "QUEIJO MUSSARELA",
                "ncm_sh_code": "04061090",
                "quantity": 100.0,
                "total_value": 3500.0,
            },
            # 2022 Data
            {
                "year": 2022,
                "emitter_uf": "SP",
                "product_service_description": "CIMENTO CP II",
                "ncm_sh_code": "25232910",
                "quantity": 100.0,
                "total_value": 3000.0,
            },
        ]

        df_raw = pd.DataFrame(raw_data)
        df_raw["total_value"] = df_raw["total_value"].astype(float)
        df_raw["quantity"] = df_raw["quantity"].astype(float)

        # Filtra pelo ano selecionado para as guias anuais
        df_year = df_raw[df_raw["year"] == selected_year].copy()

        if df_year.empty:
            return {
                "uf_data": [],
                "ncm_data": [],
                "product_data": [],
                "multi_year_data": [],
            }

        # --- Agregações para as Guias Anuais ---

        # Agregação por UF
        df_uf_agg = (
            df_year.groupby("emitter_uf")
            .agg(
                item_total_value_sum=("total_value", "sum"),
                item_count=(
                    "product_service_description",
                    "count",
                ),  # Número de linhas de item
                total_quantity=("quantity", "sum"),
            )
            .reset_index()
            .rename(columns={"emitter_uf": "GROUP_COL"})
        )

        # Agregação por NCM/SH
        df_ncm_agg = (
            df_year.groupby("ncm_sh_code")
            .agg(
                item_total_value_sum=("total_value", "sum"),
            )
            .reset_index()
            .rename(columns={"ncm_sh_code": "GROUP_COL"})
        )

        # Agregação por Produto
        df_product_agg = (
            df_year.groupby("product_service_description")
            .agg(
                item_total_value_sum=("total_value", "sum"),
            )
            .reset_index()
            .rename(columns={"product_service_description": "GROUP_COL"})
        )

        # --- Agregação Multi-Anual (APENAS por UF) ---
        df_multi_year_agg = (
            df_raw.groupby(["emitter_uf", "year"])
            .agg(
                item_total_value_sum=("total_value", "sum"),
                item_count=("product_service_description", "count"),
                total_quantity=("quantity", "sum"),
            )
            .reset_index()
        )

        return {
            "uf_data": df_uf_agg.rename(columns={"GROUP_COL": "emitter_uf"}).to_dict(
                "records"
            ),
            "ncm_data": df_ncm_agg.rename(columns={"GROUP_COL": "ncm_sh_code"}).to_dict(
                "records"
            ),
            "product_data": df_product_agg.rename(
                columns={"GROUP_COL": "product_service_description"}
            ).to_dict("records"),
            "multi_year_data": df_multi_year_agg.to_dict("records"),
        }

    def _get_data_source_key(self, tab_instance: BaseItemDashboardTab) -> str:
        if tab_instance.GROUP_BY_COLUMN == "emitter_uf":
            return "uf_data"
        elif tab_instance.GROUP_BY_COLUMN == "ncm_sh_code":
            return "ncm_data"
        elif tab_instance.GROUP_BY_COLUMN == "product_service_description":
            return "product_data"
        else:
            return "uf_data"  # Fallback

    def show(self) -> None:
        st.title("🔎 Análise Detalhada de Itens de NF-e")
        geojson = self._load_brazil_geojson()

        with st.sidebar:
            st.title("⚙️ Filtros de Dashboard")
            selected_year = st.selectbox("Selecione o Ano Fiscal", YEAR_LIST, index=0)
            selected_color_theme = st.selectbox(
                "Selecione um Esquema de Cores", COLOR_THEME_LIST, index=0
            )

        tab_titles = list(self.tabs.keys())
        st_tabs = st.tabs(tab_titles)

        with st.spinner(
            f"🚀 Analisando dados de itens para {selected_year} com o Agente de IA..."
        ):
            try:
                # Simula a obtenção de todos os dados agregados para o ano
                data = self._run_dummy_data_simulation(selected_year)
                df_multi_year = pd.DataFrame(data["multi_year_data"])

            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                st.error(f"Falha na execução do workflow de análise: {e}")
                data = {
                    "uf_data": [],
                    "ncm_data": [],
                    "product_data": [],
                    "multi_year_data": [],
                }
                df_multi_year = pd.DataFrame()

        for tab_title, st_tab in zip(tab_titles, st_tabs):
            with st_tab:
                tab_instance = self.tabs[tab_title]
                data_source_key = self._get_data_source_key(tab_instance)
                source_data = data.get(data_source_key, [])

                # 1. Monta a pergunta para o agente (com base no agrupamento)
                question_template = f"Calculate the {tab_instance.METRIC_LABEL} ({tab_instance.METRIC_COLUMN}) grouped by {tab_instance.GROUP_BY_COLUMN} for the year {selected_year}."

                if st.checkbox(
                    f"Mostrar Instruções do Agente ({tab_title})", value=False
                ):
                    agent_info = tab_instance.get_agent_format_instructions(
                        question_template
                    )
                    st.code(agent_info["input_message"], language="markdown")
                    st.code(agent_info["format_instructions_str"], language="json")

                # 2. Filtra os dados da fonte para a métrica da aba
                data_for_tab = [
                    {
                        tab_instance.GROUP_BY_COLUMN: d[tab_instance.GROUP_BY_COLUMN],
                        tab_instance.METRIC_COLUMN: d.get(tab_instance.METRIC_COLUMN),
                    }
                    for d in source_data
                    if tab_instance.METRIC_COLUMN in d
                ]

                # 3. Renderiza a guia
                tab_instance.render(
                    selected_year,
                    selected_color_theme,
                    df_multi_year,  # Envia o DF multi-anual completo para que a guia filtre
                    geojson,
                    data_for_tab,
                )
