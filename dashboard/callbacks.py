from __future__ import annotations

import pandas as pd
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc

from dashboard import charts
from dashboard.data_loader import DashData


def register(app, data: DashData) -> None:

    # ── A: year toggle → scatter + rankings ──────────────────────────────
    @app.callback(
        Output("scatter-loglog", "figure"),
        Output("hubs-chart", "figure"),
        Output("safest-chart", "figure"),
        Input("year-toggle", "value"),
    )
    def update_year_charts(ano_filter: str):
        df_taxa = data.df_taxa_2023 if ano_filter == "2023" else data.df_taxa_2024
        ano_label = ano_filter if ano_filter != "Ambos" else "2023"

        scatter = charts.fig_scatter_loglog(data.df_taxa_combined, ano_filter)
        hubs = charts.fig_hubs_inverso(df_taxa, ano_label)
        safest = charts.fig_safest(df_taxa, ano_label)
        return scatter, hubs, safest

    # ── B: year selector → populate airport dropdown ──────────────────────
    @app.callback(
        Output("dd-aeroporto", "options"),
        Output("dd-aeroporto", "value"),
        Input("dd-ano-lookup", "value"),
    )
    def update_airport_options(ano: str):
        df = data.df_taxa_2023 if ano == "2023" else data.df_taxa_2024
        df = df.sort_values("nome_aeroporto")
        options = [
            {
                "label": f"{row.aeroporto} — {row.nome_aeroporto[:60]}",
                "value": row.aeroporto,
            }
            for row in df.itertuples()
        ]
        first = options[0]["value"] if options else None
        return options, first

    # ── C: airport + year → metric card ──────────────────────────────────
    @app.callback(
        Output("airport-output", "children"),
        Input("dd-aeroporto", "value"),
        Input("dd-ano-lookup", "value"),
    )
    def update_airport_card(icao: str, ano: str):
        if not icao:
            return ""

        try:
            df = data.df_taxa_2023 if ano == "2023" else data.df_taxa_2024
            row_df = df[df["aeroporto"] == icao]
            if row_df.empty:
                return dbc.Alert("Aeroporto não encontrado.", color="warning")

            row = row_df.iloc[0]

            def _fmt(val):
                return f"{val:,.0f}".replace(",", ".")

            def _safe_positive(val) -> bool:
                return pd.notna(val) and float(val) > 0

            txt_inc = (
                f"1 ocorrencia a cada **{_fmt(1 / float(row['taxa_incidente']))}** voos"
                if _safe_positive(row["taxa_incidente"]) else "Sem registros de incidentes"
            )
            txt_grave = (
                f"1 ocorrencia a cada **{_fmt(1 / float(row['taxa_grave']))}** voos"
                if _safe_positive(row["taxa_grave"]) else "Sem registros de graves/acidentes"
            )

            df_sorted = df[df["taxa_total"] > 0].copy()
            df_sorted["rank"] = df_sorted["taxa_total"].rank(method="min").astype(int)
            rank_row = df_sorted[df_sorted["aeroporto"] == icao]
            rank_pos = int(rank_row["rank"].iloc[0]) if not rank_row.empty else "?"
            total_ranked = len(df_sorted)

            return dbc.Card(
                dbc.CardBody([
                    html.H5(
                        f"{row['aeroporto']} — {row['nome_aeroporto']}",
                        className="card-title",
                    ),
                    html.P(f"Ano: {ano}  |  Movimentos totais: {_fmt(row['movimentacao_total'])}"),
                    html.Hr(),
                    dcc.Markdown(f"**Incidentes:** {txt_inc}"),
                    dcc.Markdown(f"**Acidentes + Incidentes Graves:** {txt_grave}"),
                    html.Hr(),
                    html.P(
                        f"Posicao no ranking de taxa total: {rank_pos} de {total_ranked} aeroportos "
                        f"(1 = menor taxa)",
                        className="rank-text",
                    ),
                ]),
                className="airport-card",
            )
        except Exception as exc:
            return dbc.Alert(f"Erro: {exc}", color="danger")
