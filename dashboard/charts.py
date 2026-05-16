from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.constants import CORES, MODEL_TABLE

_ANOS = [2023, 2024]


# ── helpers ──────────────────────────────────────────────────────────────────

def _filter_years(df: pd.DataFrame, col: str, years: list[int]) -> pd.DataFrame:
    return df[df[col].dt.year.isin(years)].copy()


# ── Section 2: tendência histórica ───────────────────────────────────────────

def fig_tendencia(df_ocorrencia: pd.DataFrame) -> go.Figure:
    df = df_ocorrencia[df_ocorrencia["ocorrencia_dia"].notna()].copy()
    df["ano"] = df["ocorrencia_dia"].dt.year.astype(str)
    tabela = (
        df.groupby(["ano", "ocorrencia_classificacao"])
        .size()
        .reset_index(name="contagem")
    )
    fig = px.bar(
        tabela,
        x="ano",
        y="contagem",
        color="ocorrencia_classificacao",
        barmode="stack",
        color_discrete_map=CORES,
        labels={
            "ano": "Ano",
            "contagem": "Número de ocorrências",
            "ocorrencia_classificacao": "Classificação",
        },
        title="Ocorrências por ano — série histórica completa",
        category_orders={"ocorrencia_classificacao": ["ACIDENTE", "INCIDENTE GRAVE", "INCIDENTE"]},
    )
    fig.update_layout(height=420, legend=dict(orientation="h", y=1.08, x=0))
    return fig


# ── Section 3: mapa espacial ─────────────────────────────────────────────────

def fig_mapa(df_ocorrencia: pd.DataFrame) -> go.Figure:
    df = _filter_years(df_ocorrencia, "ocorrencia_dia", _ANOS).copy()
    df["ocorrencia_latitude"] = pd.to_numeric(df["ocorrencia_latitude"], errors="coerce")
    df["ocorrencia_longitude"] = pd.to_numeric(df["ocorrencia_longitude"], errors="coerce")
    df = df[df["ocorrencia_latitude"].notna() & df["ocorrencia_longitude"].notna()]

    counts = df["ocorrencia_classificacao"].value_counts()
    subtitle = "  ·  ".join(f"{cls}: {n}" for cls, n in counts.items())

    fig = px.scatter_map(
        df,
        lat="ocorrencia_latitude",
        lon="ocorrencia_longitude",
        hover_name="ocorrencia_cidade",
        color="ocorrencia_classificacao",
        category_orders={"ocorrencia_classificacao": ["ACIDENTE", "INCIDENTE GRAVE", "INCIDENTE"]},
        color_discrete_map=CORES,
        zoom=3.3,
        center={"lat": -14, "lon": -52},
        map_style="carto-positron",
        opacity=0.6,
        title="Ocorrências aéreas por localização — Brasil (2023–2024)",
    )
    fig.update_layout(
        height=620,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            title_text="", itemclick="toggle", itemdoubleclick="toggleothers",
        ),
        annotations=[dict(
            text=f"Total: {counts.sum()}  ·  {subtitle}",
            xref="paper", yref="paper", x=0.5, y=-0.03,
            showarrow=False, font=dict(size=12), xanchor="center", yanchor="top",
        )],
    )
    return fig


# ── Section 4: ranking por cidades ───────────────────────────────────────────

def fig_cidades(df_ocorrencia: pd.DataFrame) -> go.Figure:
    df = _filter_years(df_ocorrencia, "ocorrencia_dia", _ANOS)
    classificacoes = ["ACIDENTE", "INCIDENTE GRAVE", "INCIDENTE"]
    anos = [2023, 2024]

    fig = make_subplots(
        rows=2, cols=3,
        vertical_spacing=0.15, horizontal_spacing=0.08,
        subplot_titles=[f"{cls} — {ano}" for ano in anos for cls in classificacoes],
    )

    for row_idx, ano in enumerate(anos, start=1):
        df_ano = df[df["ocorrencia_dia"].dt.year == ano]
        for col_idx, cls in enumerate(classificacoes, start=1):
            contagens = (
                df_ano[df_ano["ocorrencia_classificacao"] == cls]
                .groupby("ocorrencia_cidade").size()
                .reset_index(name="contagem")
                .sort_values("contagem", ascending=False)
                .reset_index(drop=True)
            )
            contagens["rank"] = range(1, len(contagens) + 1)
            fig.add_trace(
                go.Scatter(
                    x=contagens["rank"],
                    y=contagens["contagem"],
                    mode="markers",
                    marker=dict(color=CORES[cls], size=6, opacity=0.7),
                    text=contagens["ocorrencia_cidade"],
                    hovertemplate="<b>%{text}</b><br>Rank: %{x}<br>Ocorrências: %{y}<extra></extra>",
                    showlegend=False,
                ),
                row=row_idx, col=col_idx,
            )
            fig.update_xaxes(title_text="Rank" if row_idx == 2 else "", row=row_idx, col=col_idx)
            fig.update_yaxes(title_text="Ocorrências" if col_idx == 1 else "", row=row_idx, col=col_idx)

    fig.update_layout(height=620, title_text="Ranking de ocorrências por cidade — 2023 e 2024")
    return fig


# ── Section 5: fase de voo (treemap) ─────────────────────────────────────────

def fig_fase_treemap(df_ocorrencia: pd.DataFrame, df_aeronave: pd.DataFrame) -> go.Figure:
    df_fase = df_aeronave[df_aeronave["aeronave_fase_operacao"].notna()]
    df_com_fase = df_ocorrencia.merge(
        df_fase[["codigo_ocorrencia2", "aeronave_fase_operacao"]],
        on="codigo_ocorrencia2", how="inner",
    )
    df_com_fase = _filter_years(df_com_fase, "ocorrencia_dia", _ANOS)

    partes = []
    for ano in _ANOS:
        sub = df_com_fase[df_com_fase["ocorrencia_dia"].dt.year == ano]
        cnt = (
            sub.groupby("aeronave_fase_operacao").size()
            .reset_index(name="contagem")
            .assign(ano=str(ano))
        )
        partes.append(cnt)

    df_tree = pd.concat(partes, ignore_index=True)
    df_tree["total_ocorrencias"] = "Ocorrências (2023–2024)"

    fig = px.treemap(
        df_tree,
        path=["total_ocorrencias", "ano", "aeronave_fase_operacao"],
        values="contagem",
        color="contagem",
        color_continuous_scale="Blues",
        hover_data={"contagem": ":,.0f"},
        title="Distribuição de ocorrências por ano e fase de operação",
    )
    fig.update_traces(
        textinfo="label+value+percent parent",
        textfont_size=12,
        marker=dict(line=dict(width=0.5, color="white")),
    )
    fig.update_layout(height=520, margin=dict(t=48, l=8, r=8, b=8))
    return fig


# ── Section 6: histograma de movimentos ──────────────────────────────────────

def fig_histograma_movimentos(df_t23: pd.DataFrame, df_t24: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=1, cols=2, subplot_titles=("2023", "2024"))
    for col, (df, ano) in enumerate([(df_t23, "2023"), (df_t24, "2024")], start=1):
        fig.add_trace(
            go.Histogram(
                x=df["movimentacao_total"].astype(float),
                nbinsx=35,
                name=ano,
                marker_color="#636EFA",
                opacity=0.85,
                showlegend=False,
            ),
            row=1, col=col,
        )
    fig.update_xaxes(title_text="Movimentos totais (pousos + decolagens)", row=1, col=1)
    fig.update_yaxes(title_text="Frequência (nº de aeroportos)", row=1, col=1)
    fig.update_layout(height=380, title_text="Distribuição de aeroportos por volume de movimentos")
    return fig


# ── Section 7a: movimentos mensais (barras) ───────────────────────────────────

def fig_movimentos_mensais(df_mensal: pd.DataFrame) -> go.Figure:
    df = df_mensal.copy()
    df["ano"] = df["ano_mes"].dt.year
    df["mes_lab"] = df["ano_mes"].dt.strftime("%b")

    fig = make_subplots(rows=1, cols=2, subplot_titles=("2023", "2024"), horizontal_spacing=0.06)
    for col, ano in enumerate([2023, 2024], start=1):
        sub = df[df["ano"] == ano].sort_values("ano_mes")
        fig.add_trace(
            go.Bar(x=sub["mes_lab"], y=sub["total_movimentos"],
                   marker_color="#0d214f", opacity=0.85, showlegend=False),
            row=1, col=col,
        )
    fig.update_yaxes(title_text="Movimentos realizados", row=1, col=1)
    fig.update_layout(height=340, title_text="Movimentos mensais realizados — VRA/ANAC")
    return fig


# ── Section 7b: taxa mensal (linhas) ─────────────────────────────────────────

def fig_taxa_mensal(df_mensal: pd.DataFrame) -> go.Figure:
    df = df_mensal.copy()
    labels = df["ano_mes"].dt.strftime("%b/%y")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=df["taxa_ocorrencias"],
        mode="lines+markers", name="Taxa geral",
        line=dict(color="#636EFA", width=2.5),
    ))
    for cls, cor in CORES.items():
        col = cls
        if col in df.columns:
            taxa_cls = df[col] / df["total_movimentos"]
            fig.add_trace(go.Scatter(
                x=labels, y=taxa_cls,
                mode="lines", name=cls,
                line=dict(color=cor, width=1.5, dash="dot"),
            ))
    fig.update_layout(
        height=360,
        title="Taxa mensal de ocorrências por movimento (2023–2024)",
        yaxis_title="Ocorrências / movimento",
        legend=dict(orientation="h", y=1.1, x=0),
    )
    return fig


# ── Section 8: PPM por aeroporto ─────────────────────────────────────────────

def fig_ppm_linhas(df_t23: pd.DataFrame, df_t24: pd.DataFrame) -> go.Figure:
    def _prep(df):
        d = df[df["movimentacao_total"] >= 100].sort_values("movimentacao_total").reset_index(drop=True)
        d["ordem"] = np.arange(1, len(d) + 1)
        d["ppm_total"] = d["taxa_total"] * 1_000_000
        d["ppm_grave"] = d["taxa_grave"] * 1_000_000
        d["ppm_incidente"] = d["taxa_incidente"] * 1_000_000
        return d

    fig = make_subplots(rows=1, cols=2, subplot_titles=("2023", "2024"),
                        horizontal_spacing=0.07, shared_yaxes=True)

    for col, (df_src, show_leg) in enumerate([(df_t23, True), (df_t24, False)], start=1):
        d = _prep(df_src)
        cd = np.stack([d["aeroporto"].astype(str), d["movimentacao_total"].to_numpy()], axis=-1)

        for name, y_col, cor, lg in [
            ("Taxa total (ppm)", "ppm_total", "#636EFA", "tot"),
            ("Taxa grave (ppm)", "ppm_grave", "rgba(239,85,59,0.45)", "grave"),
            ("Taxa incidente (ppm)", "ppm_incidente", "rgba(39,211,245,0.45)", "inc"),
        ]:
            fig.add_trace(go.Scatter(
                x=d["ordem"], y=d[y_col], mode="lines", name=name,
                text=d["nome_aeroporto"], customdata=cd,
                line=dict(color=cor, width=2 if lg == "tot" else 1.5),
                hovertemplate="<b>%{text}</b> (%{customdata[0]})<br>"
                              "Movimentos: %{customdata[1]:,.0f}<br>"
                              f"{name}: %{{y:,.1f}}<extra></extra>",
                showlegend=show_leg, legendgroup=lg,
            ), row=1, col=col)

    fig.update_xaxes(title_text="Aeroporto (menor → maior movimentação)", row=1, col=1)
    fig.update_yaxes(title_text="Ocorrências por milhão de movimentos (ppm)", row=1, col=1)
    fig.update_layout(height=420, title_text="Taxa de ocorrência em PPM por aeroporto",
                      legend=dict(orientation="h", y=1.1, x=0))
    return fig


# ── Section 9: tabela descritiva de taxas ────────────────────────────────────

def fig_tabela_taxas(df_t23: pd.DataFrame, df_t24: pd.DataFrame) -> go.Figure:
    cols = ["taxa_total", "taxa_incidente", "taxa_grave"]

    def _resumo(df, ano):
        rows = []
        for col in cols:
            s = df[col].dropna()
            rows.append({
                "Ano": ano,
                "Variável": col,
                "Média": f"{s.mean():.6f}",
                "Mediana": f"{s.median():.6f}",
                "Desvio Padrão": f"{s.std():.6f}",
                "Amplitude": f"{(s.max() - s.min()):.6f}",
            })
        return rows

    data = _resumo(df_t23, 2023) + _resumo(df_t24, 2024)
    df = pd.DataFrame(data)

    fig = go.Figure(go.Table(
        header=dict(values=list(df.columns), fill_color="#0d214f",
                    font=dict(color="white", size=12), align="left"),
        cells=dict(values=[df[c] for c in df.columns], fill_color="lavender",
                   align="left", font=dict(size=11)),
    ))
    fig.update_layout(height=340, margin=dict(t=10, b=10))
    return fig


# ── Section 10: scatter log-log ───────────────────────────────────────────────

def fig_scatter_loglog(df_combined: pd.DataFrame, ano_filter: str = "Ambos") -> go.Figure:
    if ano_filter == "Ambos":
        df = df_combined.copy()
    else:
        df = df_combined[df_combined["ano"] == ano_filter].copy()

    if "nome_aeroporto" not in df.columns:
        df["nome_aeroporto"] = df["aeroporto"]

    p50 = df["taxa_total"].quantile(0.50)
    p75 = df["taxa_total"].quantile(0.75)

    x_min = df["movimentacao_total"].min()
    x_max = df["movimentacao_total"].max()
    x_range = np.logspace(np.log10(max(x_min, 1)), np.log10(x_max), 200)

    cores_anos = {"2023": "#636EFA", "2024": "#EF553B"}
    fig = go.Figure()

    for ano in sorted(df["ano"].unique()):
        cor = cores_anos.get(ano, "#888")
        sub = df[df["ano"] == ano]
        fig.add_trace(go.Scatter(
            x=sub["movimentacao_total"], y=sub["total_ocorrencias"],
            mode="markers", name=ano,
            text=sub["nome_aeroporto"], customdata=sub["aeroporto"],
            hovertemplate="<b>%{text}</b> (%{customdata})<br>"
                          "Movimentos: %{x:,.0f}<br>Ocorrências: %{y}<extra></extra>",
            marker=dict(color=cor, opacity=0.7, size=7),
        ))

    fig.add_trace(go.Scatter(
        x=x_range, y=p50 * x_range, mode="lines",
        name=f"P50 — taxa típica ({p50:.5f})",
        line=dict(color="gray", dash="dash", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=p75 * x_range, mode="lines",
        name=f"P75 — risco elevado ({p75:.5f})",
        line=dict(color="orange", dash="dot", width=2),
    ))

    fig.update_layout(
        title="Movimentos vs ocorrências por aeroporto (escala log-log)",
        xaxis=dict(title="Total de movimentos (log)", type="log"),
        yaxis=dict(title="Total de ocorrências (log)", type="log"),
        legend=dict(orientation="h", y=1.1, x=0),
        height=520,
    )
    return fig


# ── Section 11: tabela de modelos ─────────────────────────────────────────────

def fig_tabela_modelos() -> go.Figure:
    df = pd.DataFrame(MODEL_TABLE)
    fig = go.Figure(go.Table(
        header=dict(
            values=["Modelo", "AIC", "Log-likelihood", "Deviance ratio", "Pearson ratio", "Intercepto"],
            fill_color="#0d214f", font=dict(color="white", size=12), align="left",
        ),
        cells=dict(
            values=[
                df["modelo"], df["AIC"], df["log_likelihood"],
                df["deviance_ratio"], df["pearson_ratio"], df["intercepto"],
            ],
            fill_color=[["#e8f4e8", "lavender"]],
            align="left", font=dict(size=11),
        ),
    ))
    fig.update_layout(height=160, margin=dict(t=8, b=8))
    return fig


# ── Section 12: rankings ──────────────────────────────────────────────────────

def fig_hubs_inverso(df_taxa: pd.DataFrame, ano: str) -> go.Figure:
    top = df_taxa.nlargest(5, "movimentacao_total").copy()
    if "nome_aeroporto" not in top.columns:
        top["nome_aeroporto"] = top["aeroporto"]

    top["voos_por_grave"] = (1 / top["taxa_grave"]).replace([np.inf], pd.NA)
    top["voos_por_incidente"] = (1 / top["taxa_incidente"]).replace([np.inf], pd.NA)

    df_m = top.melt(
        id_vars=["aeroporto", "nome_aeroporto", "movimentacao_total"],
        value_vars=["voos_por_grave", "voos_por_incidente"],
        var_name="tipo", value_name="voos_por_ocorrencia",
    )
    df_m["tipo"] = df_m["tipo"].map({
        "voos_por_grave": "Graves (Acidentes + Inc. Graves)",
        "voos_por_incidente": "Incidentes",
    })
    df_m["rotulo"] = df_m["voos_por_ocorrencia"].apply(
        lambda x: f"1 em {x:,.0f} voos" if pd.notna(x) else "sem ocorrências"
    )
    order = top.sort_values("movimentacao_total", ascending=True)["nome_aeroporto"].tolist()

    fig = px.bar(
        df_m.dropna(subset=["voos_por_ocorrencia"]),
        x="voos_por_ocorrencia", y="nome_aeroporto", color="tipo",
        orientation="h", barmode="group", text="rotulo",
        title=f"{ano} — Intervalo médio entre ocorrências (5 aeroportos mais movimentados)",
        labels={"voos_por_ocorrencia": "Voos por ocorrência  ·  maior = mais seguro",
                "nome_aeroporto": "Aeroporto", "tipo": "Tipo"},
        color_discrete_map={
            "Graves (Acidentes + Inc. Graves)": CORES["ACIDENTE"],
            "Incidentes": CORES["INCIDENTE"],
        },
        category_orders={"nome_aeroporto": order},
        height=400,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0), margin=dict(r=100))
    return fig


def fig_safest(df_taxa: pd.DataFrame, ano: str) -> go.Figure:
    candidatos = df_taxa[df_taxa["taxa_total"] > 0].copy()
    top = candidatos.nsmallest(5, "taxa_total").copy()
    if "nome_aeroporto" not in top.columns:
        top["nome_aeroporto"] = top["aeroporto"]

    top["voos_por_grave"] = (1 / top["taxa_grave"]).replace([np.inf], pd.NA)
    top["voos_por_incidente"] = (1 / top["taxa_incidente"]).replace([np.inf], pd.NA)

    df_m = top.melt(
        id_vars=["aeroporto", "nome_aeroporto", "movimentacao_total"],
        value_vars=["voos_por_grave", "voos_por_incidente"],
        var_name="tipo", value_name="voos_por_ocorrencia",
    )
    df_m["tipo"] = df_m["tipo"].map({
        "voos_por_grave": "Graves (Acidentes + Inc. Graves)",
        "voos_por_incidente": "Incidentes",
    })
    df_m["rotulo"] = df_m["voos_por_ocorrencia"].apply(
        lambda x: f"1 em {x:,.0f} voos" if pd.notna(x) else "sem ocorrências"
    )
    order = top.sort_values("taxa_total", ascending=False)["nome_aeroporto"].tolist()

    fig = px.bar(
        df_m.dropna(subset=["voos_por_ocorrencia"]),
        x="voos_por_ocorrencia", y="nome_aeroporto", color="tipo",
        orientation="h", barmode="group", text="rotulo",
        title=f"{ano} — Top 5 aeroportos mais seguros (menor taxa de ocorrência)",
        labels={"voos_por_ocorrencia": "Voos por ocorrência  ·  maior = mais seguro",
                "nome_aeroporto": "Aeroporto", "tipo": "Tipo"},
        color_discrete_map={
            "Graves (Acidentes + Inc. Graves)": CORES["ACIDENTE"],
            "Incidentes": CORES["INCIDENTE"],
        },
        category_orders={"nome_aeroporto": order},
        height=400,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0), margin=dict(r=100))
    return fig


# ── Section 13: taxa por tipo de operação ────────────────────────────────────

def fig_dot_operacao(df_ocorrencia: pd.DataFrame, df_aeronave: pd.DataFrame) -> go.Figure:
    candidatas = [
        "aeronave_tipo_operacao", "aeronave_tipo_veiculo",
        "aeronave_tipo_voo", "ocorrencia_tipo_operacao",
    ]
    col_tipo = next((c for c in candidatas if c in df_aeronave.columns), None)
    if col_tipo is None:
        return go.Figure()

    df_oc = df_ocorrencia[
        df_ocorrencia["ocorrencia_dia"].dt.year.isin([2023, 2024])
    ][["codigo_ocorrencia2", "ocorrencia_classificacao", "ocorrencia_dia"]].copy()

    base = df_oc.merge(
        df_aeronave[["codigo_ocorrencia2", col_tipo]],
        on="codigo_ocorrencia2", how="inner",
    )
    base = base[base[col_tipo].notna()]

    resumo = (
        base.groupby(col_tipo)
        .agg(
            total_ocorrencias=("ocorrencia_classificacao", "size"),
            acidentes=("ocorrencia_classificacao", lambda s: (s == "ACIDENTE").sum()),
        )
        .reset_index()
    )
    resumo["taxa_acidente"] = resumo["acidentes"] / resumo["total_ocorrencias"]
    resumo["taxa_pct"] = (100 * resumo["taxa_acidente"]).round(2)
    resumo = resumo[resumo["total_ocorrencias"] >= 10].sort_values("taxa_acidente")

    fig = px.scatter(
        resumo,
        x="taxa_acidente", y=col_tipo,
        size="total_ocorrencias",
        color="taxa_acidente",
        color_continuous_scale="OrRd",
        labels={
            "taxa_acidente": "Taxa de acidentes",
            col_tipo: "Tipo de operação",
            "total_ocorrencias": "Total de ocorrências",
        },
        title="Taxa de acidentes por tipo de operação (2023–2024)",
    )
    fig.update_traces(
        text=resumo["taxa_pct"].astype(str) + "%",
        textposition="middle right",
        marker=dict(opacity=0.85, line=dict(width=0.5, color="DarkSlateGrey")),
        hovertemplate=(
            "<b>%{y}</b><br>Taxa de acidentes: %{x:.2%}<br>"
            "Total de ocorrências: %{marker.size:,}<extra></extra>"
        ),
    )
    fig.update_layout(height=480, xaxis_tickformat=".0%", coloraxis_colorbar_title="Taxa")
    return fig
