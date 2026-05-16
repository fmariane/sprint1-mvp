from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

CENIPA_OC = ROOT / "data/raw/CENIPA_FAB/ocorrencia.csv"
CENIPA_AE = ROOT / "data/raw/CENIPA_FAB/aeronave.csv"
TAXA_2023 = ROOT / "data/processed/taxa_ocorrencia_aeroporto_2023.csv"
TAXA_2024 = ROOT / "data/processed/taxa_ocorrencia_aeroporto_2024.csv"
MENSAL = ROOT / "data/processed/taxa_mensal_2023_2024.csv"


@dataclass
class DashData:
    df_ocorrencia: pd.DataFrame
    df_aeronave: pd.DataFrame
    df_taxa_2023: pd.DataFrame
    df_taxa_2024: pd.DataFrame
    df_taxa_combined: pd.DataFrame
    df_mensal: pd.DataFrame


def load_all() -> DashData:
    df_oc = pd.read_csv(CENIPA_OC, sep=";", encoding="latin1")
    df_oc["ocorrencia_dia"] = pd.to_datetime(
        df_oc["ocorrencia_dia"], format="%d/%m/%Y", dayfirst=True, errors="coerce"
    )
    df_oc = df_oc[
        pd.to_numeric(df_oc.get("ocorrencia_latitude", pd.Series(dtype=float)), errors="coerce").notna()
        | df_oc["ocorrencia_dia"].notna()
    ].copy()

    df_ae = pd.read_csv(CENIPA_AE, sep=";", encoding="latin1")

    df_t23 = pd.read_csv(TAXA_2023, sep=";")
    df_t24 = pd.read_csv(TAXA_2024, sep=";")

    df_combined = pd.concat(
        [df_t23.assign(ano="2023"), df_t24.assign(ano="2024")],
        ignore_index=True,
    )

    df_mensal = pd.read_csv(MENSAL, sep=";")
    df_mensal["ano_mes"] = pd.to_datetime(df_mensal["ano_mes"])

    return DashData(
        df_ocorrencia=df_oc,
        df_aeronave=df_ae,
        df_taxa_2023=df_t23,
        df_taxa_2024=df_t24,
        df_taxa_combined=df_combined,
        df_mensal=df_mensal,
    )
