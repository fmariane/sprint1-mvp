#!/usr/bin/env python3
"""
One-time export: build data/processed/taxa_mensal_2023_2024.csv

Columns produced:
  ano_mes, total_ocorrencias, total_movimentos, taxa_ocorrencias,
  ACIDENTE, INCIDENTE GRAVE, INCIDENTE
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "source"))

import pandas as pd

CENIPA_PATH = ROOT / "data/raw/CENIPA_FAB/ocorrencia.csv"
VRA_2023_DIR = ROOT / "data/raw/VRA/2023"
VRA_2024_DIR = ROOT / "data/raw/VRA/2024"
OUT_PATH = ROOT / "data/processed/taxa_mensal_2023_2024.csv"

VRA_USECOLS = ["Referência", "Situação Voo"]


def load_ocorrencias_mensais() -> pd.DataFrame:
    df = pd.read_csv(CENIPA_PATH, sep=";", encoding="latin1",
                     usecols=["ocorrencia_dia", "ocorrencia_classificacao"])
    df["ocorrencia_dia"] = pd.to_datetime(df["ocorrencia_dia"], format="%d/%m/%Y",
                                          dayfirst=True, errors="coerce")
    df = df[df["ocorrencia_dia"].dt.year.isin([2023, 2024]) & df["ocorrencia_dia"].notna()]
    df["ano_mes"] = df["ocorrencia_dia"].dt.to_period("M").dt.to_timestamp()

    total = df.groupby("ano_mes").size().reset_index(name="total_ocorrencias")
    por_cls = (
        df.groupby(["ano_mes", "ocorrencia_classificacao"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ("ACIDENTE", "INCIDENTE GRAVE", "INCIDENTE"):
        if col not in por_cls.columns:
            por_cls[col] = 0
    return total.merge(por_cls[["ano_mes", "ACIDENTE", "INCIDENTE GRAVE", "INCIDENTE"]],
                       on="ano_mes", how="left")


def load_movimentos_mensais() -> pd.DataFrame:
    frames = []
    for path in sorted(VRA_2023_DIR.glob("VRA_2023_*.csv")):
        frames.append(pd.read_csv(path, sep=";", encoding="utf-8", usecols=VRA_USECOLS))
    for path in sorted(VRA_2024_DIR.glob("VRA_2024_*.csv")):
        frames.append(pd.read_csv(path, sep=";", encoding="utf-8", usecols=VRA_USECOLS))

    df = pd.concat(frames, ignore_index=True)
    df = df[df["Situação Voo"] == "REALIZADO"].copy()
    df["data_movimento"] = pd.to_datetime(df["Referência"], errors="coerce")
    df = df[df["data_movimento"].notna()]
    df["ano_mes"] = df["data_movimento"].dt.to_period("M").dt.to_timestamp()
    return df.groupby("ano_mes").size().reset_index(name="total_movimentos")


def main() -> None:
    print("Loading CENIPA monthly occurrences...")
    oc = load_ocorrencias_mensais()

    print("Loading VRA monthly movements (24 files)...")
    mov = load_movimentos_mensais()

    merged = oc.merge(mov, on="ano_mes", how="inner").sort_values("ano_mes")
    merged["taxa_ocorrencias"] = merged["total_ocorrencias"] / merged["total_movimentos"]
    merged["ano_mes"] = merged["ano_mes"].astype(str)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT_PATH, sep=";", index=False)
    print(f"Exported {len(merged)} rows → {OUT_PATH}")
    print(merged.head())


if __name__ == "__main__":
    main()
