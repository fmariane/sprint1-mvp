from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard import charts
from dashboard.constants import NARRATIVAS
from dashboard.data_loader import DashData


def _section(title: str, narrative: str, *children) -> html.Div:
    return html.Div(
        [
            html.H2(title, className="section-title"),
            dcc.Markdown(narrative, className="narrative"),
            *children,
            html.Hr(className="section-hr"),
        ],
        className="section",
    )


def _kpi_card(label: str, value: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.P(label, className="kpi-label"),
            html.H3(value, className="kpi-value"),
        ]),
        className="kpi-card",
    )


def build(data: DashData) -> html.Div:
    total_oc = len(data.df_taxa_combined)
    n_aeroportos = data.df_taxa_combined["aeroporto"].nunique()
    mediana_taxa = data.df_taxa_combined["taxa_total"].median()

    return html.Div(
        [
            # ── Header ────────────────────────────────────────────────────
            html.Div(
                [
                    html.H1(
                        "Panorama da Segurança Operacional nos Aeroportos do Brasil",
                        className="main-title",
                    ),
                    html.P(NARRATIVAS["header_sub"], className="main-sub"),
                    dbc.Row([
                        dbc.Col(_kpi_card("Registros de taxa aeroporto (2023–2024)",
                                          str(total_oc)), md=4),
                        dbc.Col(_kpi_card("Aeroportos com dados de taxa",
                                          str(n_aeroportos)), md=4),
                        dbc.Col(_kpi_card("Taxa mediana de ocorrência",
                                          f"{mediana_taxa:.5f}"), md=4),
                    ], className="kpi-row"),
                ],
                className="header-block",
            ),
            html.Hr(className="section-hr"),

            # ── S2: Tendência histórica ────────────────────────────────────
            _section(
                "Evolução das Ocorrências",
                NARRATIVAS["tendencia"],
                dcc.Graph(
                    figure=charts.fig_tendencia(data.df_ocorrencia),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S3: Mapa espacial ──────────────────────────────────────────
            _section(
                "Distribuição Geográfica (2023–2024)",
                NARRATIVAS["mapa"],
                dcc.Graph(figure=charts.fig_mapa(data.df_ocorrencia)),
            ),

            # ── S4: Ranking por cidades ────────────────────────────────────
            _section(
                "Ocorrências por Cidade e Classificação",
                NARRATIVAS["cidades"],
                dcc.Graph(
                    figure=charts.fig_cidades(data.df_ocorrencia),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S5: Fase de voo ────────────────────────────────────────────
            _section(
                "Distribuição por Fase de Voo",
                NARRATIVAS["fase"],
                dcc.Graph(
                    figure=charts.fig_fase_treemap(data.df_ocorrencia, data.df_aeronave),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S6: Histograma de movimentos ───────────────────────────────
            _section(
                "Concentração de Movimentos nos Hubs",
                NARRATIVAS["hubs"],
                dcc.Graph(
                    figure=charts.fig_histograma_movimentos(data.df_taxa_2023, data.df_taxa_2024),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S7: Evolução mensal ────────────────────────────────────────
            _section(
                "Evolução Mensal (2023–2024)",
                NARRATIVAS["mensal"],
                dcc.Graph(
                    figure=charts.fig_movimentos_mensais(data.df_mensal),
                    config={"displayModeBar": False},
                ),
                dcc.Graph(
                    figure=charts.fig_taxa_mensal(data.df_mensal),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S8: PPM por aeroporto ──────────────────────────────────────
            _section(
                "Taxa de Ocorrência em PPM por Aeroporto",
                NARRATIVAS["ppm"],
                dcc.Graph(
                    figure=charts.fig_ppm_linhas(data.df_taxa_2023, data.df_taxa_2024),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S9: Estatísticas descritivas ───────────────────────────────
            html.Div(
                [
                    html.H2("Estatísticas Descritivas das Taxas", className="section-title"),
                    dcc.Graph(
                        figure=charts.fig_tabela_taxas(data.df_taxa_2023, data.df_taxa_2024),
                        config={"displayModeBar": False},
                    ),
                    html.Hr(className="section-hr"),
                ],
                className="section",
            ),

            # ── S10: Scatter log-log (interativo) ─────────────────────────
            html.Div(
                [
                    html.H2("Resultado Central: Movimentos vs Ocorrências (log-log)",
                            className="section-title"),
                    dcc.Markdown(NARRATIVAS["scatter"], className="narrative"),
                    html.Div(
                        [
                            html.Label("Filtrar por ano:", className="toggle-label"),
                            dcc.RadioItems(
                                id="year-toggle",
                                options=[
                                    {"label": "2023", "value": "2023"},
                                    {"label": "2024", "value": "2024"},
                                    {"label": "Ambos", "value": "Ambos"},
                                ],
                                value="Ambos",
                                inline=True,
                                className="year-radio",
                            ),
                        ],
                        className="toggle-row",
                    ),
                    dcc.Graph(id="scatter-loglog",
                              figure=charts.fig_scatter_loglog(data.df_taxa_combined, "Ambos")),
                    html.Hr(className="section-hr"),
                ],
                className="section",
            ),

            # ── S11: Modelos de contagem ───────────────────────────────────
            _section(
                "Confirmação Estatística: Poisson vs Binomial Negativa",
                NARRATIVAS["modelos"],
                dcc.Graph(
                    figure=charts.fig_tabela_modelos(),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S12: Rankings (interativo) ─────────────────────────────────
            html.Div(
                [
                    html.H2("Rankings de Segurança por Aeroporto", className="section-title"),
                    dcc.Markdown(NARRATIVAS["rankings"], className="narrative"),
                    dcc.Graph(id="hubs-chart",
                              figure=charts.fig_hubs_inverso(data.df_taxa_2023, "2023")),
                    dcc.Graph(id="safest-chart",
                              figure=charts.fig_safest(data.df_taxa_2023, "2023")),
                    html.Hr(className="section-hr"),
                ],
                className="section",
            ),

            # ── S13: Limitações ────────────────────────────────────────────
            _section(
                "Limitações do Estudo",
                NARRATIVAS["limitacoes"],
                dcc.Graph(
                    figure=charts.fig_dot_operacao(data.df_ocorrencia, data.df_aeronave),
                    config={"displayModeBar": False},
                ),
            ),

            # ── S14: Explorar aeroporto ────────────────────────────────────
            html.Div(
                [
                    html.H2("Explorar: Busca por Aeroporto", className="section-title"),
                    dcc.Markdown(NARRATIVAS["lookup"], className="narrative"),
                    dbc.Row([
                        dbc.Col(
                            dcc.Dropdown(
                                id="dd-ano-lookup",
                                options=[{"label": "2023", "value": "2023"},
                                         {"label": "2024", "value": "2024"}],
                                value="2023",
                                clearable=False,
                                placeholder="Ano",
                            ),
                            md=2,
                        ),
                        dbc.Col(
                            dcc.Dropdown(id="dd-aeroporto", placeholder="Selecione um aeroporto..."),
                            md=10,
                        ),
                    ], className="lookup-row"),
                    html.Div(id="airport-output", className="airport-output"),
                    html.Hr(className="section-hr"),
                ],
                className="section",
            ),

            # ── S15: Referências ───────────────────────────────────────────
            html.Div(
                [
                    html.H2("Referências", className="section-title"),
                    dcc.Markdown(
                        """
- INTERNATIONAL CIVIL AVIATION ORGANIZATION. *Safety Management Manual (SMM)*. 4. ed. Montreal: ICAO, 2018.
- CENIPA/FAB. Base de ocorrências aeronáuticas. Disponível em: dados.gov.br.
- ANAC. Registro de Voos em Rota (VRA). Disponível em: dados.gov.br.
                        """,
                        className="narrative",
                    ),
                ],
                className="section",
            ),
        ],
        className="main-container",
    )
