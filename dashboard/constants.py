from __future__ import annotations

CORES: dict[str, str] = {
    "ACIDENTE": "#EF553B",
    "INCIDENTE GRAVE": "#f7a831",
    "INCIDENTE": "#27D3F5",
}

# Extracted from mvp.ipynb cells 50/52/53 (last executed output, 2023-2024 data)
MODEL_TABLE = [
    {
        "modelo": "GLM NegBin + offset(log_movimentos)",
        "AIC": 348.44,
        "log_likelihood": -173.22,
        "deviance_ratio": "—",
        "pearson_ratio": "—",
        "intercepto": -10.07,
    },
    {
        "modelo": "Poisson + offset(log_movimentos)",
        "AIC": 405.09,
        "log_likelihood": -201.54,
        "deviance_ratio": 3.24,
        "pearson_ratio": 1568.96,
        "intercepto": -11.41,
    },
]

# NegBin practical interpretation: exp(-10.071) ≈ 4.2e-5 accidents/movement
NEGBIN_RATE_PER_100K = round(2.58e-5 * 100_000, 4)  # ~2.58 accidents per 100k movements

NARRATIVAS = {
    "header_sub": "Uma análise baseada em ocorrências aeronáuticas (CENIPA/FAB) e exposição operacional (ANAC VRA) — 2023 e 2024.",
    "tendencia": (
        "A série histórica mostra que o volume de ocorrências oscilou até 2022, "
        "com incidentes dominando a contagem. O período 2023–2024 apresenta nível elevado "
        "de registros, justificando o foco deste estudo. Acidentes mantêm trajetória estável "
        "e em baixo volume ao longo de toda a série."
    ),
    "mapa": (
        "A distribuição geográfica revela concentração de ocorrências no Centro-Sul do país, "
        "compatível com a densidade do tráfego aéreo regular. Use os controles da legenda para "
        "filtrar por classificação."
    ),
    "cidades": (
        "Acidentes têm distribuição uniforme e em baixo volume por cidade — a maioria registra "
        "apenas 1 evento. Incidentes são altamente concentrados: poucas cidades (grandes hubs) "
        "dominam a contagem, tornando a média enganosa como medida central."
    ),
    "fase": (
        "Aproximação, pouso e decolagem concentram a maior parte das ocorrências — padrão "
        "consistente com a literatura de segurança operacional. A fase de cruzeiro, apesar do "
        "maior tempo de exposição, apresenta proporcionalmente menos eventos."
    ),
    "hubs": (
        "A distribuição de movimentos por aeroporto é fortemente assimétrica à direita: "
        "a mediana (~520 movimentos) é cerca de 17× menor que a média (~9.000). "
        "Poucos hubs como Guarulhos, Congonhas e Galeão respondem por parcela desproporcional "
        "do tráfego total — o que motiva a normalização por exposição."
    ),
    "mensal": (
        "A evolução mensal da taxa geral (ocorrências/movimentos) mostra variação moderada ao "
        "longo de 2023 e 2024, sem tendência sustentada de alta ou baixa. "
        "O padrão de incidentes acompanha a taxa geral; acidentes e incidentes graves "
        "permanecem em volume muito inferior."
    ),
    "ppm": (
        "Em escala de partes por milhão (ppm), a heterogeneidade entre aeroportos é visível: "
        "aeroportos menores tendem a apresentar taxas mais voláteis, enquanto grandes hubs "
        "estabilizam em faixas mais baixas. O padrão confirma o efeito de diluição por volume."
    ),
    "scatter": (
        "**Resultado central.** Em escala log-log, a relação entre movimentos e ocorrências "
        "revela se o crescimento é proporcional (inclinação = 1) ou se existe efeito de diluição. "
        "Aeroportos acima da linha P75 têm taxa de ocorrência no quartil superior para o seu volume "
        "— sinal de risco relativo elevado independente do porte."
    ),
    "modelos": (
        "O modelo Poisson apresenta sobredispersão relevante (deviance_ratio ≈ 3,24; "
        "pearson_ratio ≈ 1.569), indicando que a variância dos dados é muito maior do que "
        "o modelo assume. A Binomial Negativa, com AIC menor (348 vs 405) e melhor "
        "log-verossimilhança, é adotada como modelo de inferência principal. "
        "O intercepto NegBin (−10,07) equivale a uma taxa base de aproximadamente "
        "**2,58 acidentes por 100 mil movimentos**."
    ),
    "rankings": (
        "Normalizando por movimentos, grandes hubs não são necessariamente os mais perigosos. "
        "O intervalo médio entre ocorrências (escala inversa da taxa) mostra que aeroportos "
        "de alto volume operam com frequências de evento muito mais baixas por voo — "
        "reforçando a hipótese de efeito de diluição."
    ),
    "limitacoes": (
        "O VRA cobre apenas aviação regular comercial. A aviação geral (aeronaves privadas, "
        "táxi aéreo, instrução) não está representada na exposição, o que pode inflar as taxas "
        "de aeroportos com perfil misto. O gráfico abaixo ilustra que a aviação regular "
        "apresenta a menor taxa de acidentes por tipo de operação."
    ),
    "lookup": (
        "Selecione um ano e um aeroporto para ver sua taxa de ocorrência e posição no ranking."
    ),
}
