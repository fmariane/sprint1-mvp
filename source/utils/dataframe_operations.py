from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def filter_by_year(
    df: pd.DataFrame,
    date_col: str,
    years: list[int],
    date_format: str = "%d/%m/%Y",
) -> pd.DataFrame:
    """Return rows whose *date_col* year is in *years*.

    Converts *date_col* to datetime in-place (idempotent if already datetime).
    """
    df[date_col] = pd.to_datetime(df[date_col], format=date_format, errors="coerce")
    return df[df[date_col].dt.year.isin(years)]


def load_datasource_urls(json_path: str | Path | None = None) -> dict[str, str]:
    """Load URL map from JSON. Keys are logical names; values are CSV URLs or paths."""
    if json_path is None:
        json_path = Path(__file__).resolve().parent / "datasources.json"
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"Datasource map not found: {path}")
    with path.open(encoding="utf-8") as f:
        data: Any = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}, got {type(data).__name__}")
    return {str(k): str(v) for k, v in data.items()}


def _load_fase_para_ponta(json_path: str | Path | None = None) -> dict[str, str]:
    """Load the flight-phase → airport-column mapping from JSON."""
    if json_path is None:
        json_path = Path(__file__).resolve().parent / "map_fase_airport.json"
    with Path(json_path).open(encoding="utf-8") as f:
        return json.load(f)


def resolve_aeroporto(
    df_com_fase: pd.DataFrame,
    df_aeronave: pd.DataFrame,
    fase_para_ponta: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Merge occurrence+phase data with aircraft origin/destination and resolve
    the airport where the occurrence most likely happened.

    Returns a copy of *df_com_fase* with added columns:
    ``aeronave_voo_origem``, ``aeronave_voo_destino``, ``ponta``, ``aeroporto``.
    """
    if fase_para_ponta is None:
        fase_para_ponta = _load_fase_para_ponta()

    aeronave_aeroportos = df_aeronave[
        ["codigo_ocorrencia2", "aeronave_fase_operacao",
         "aeronave_voo_origem", "aeronave_voo_destino"]
    ].drop_duplicates()

    df = df_com_fase.merge(
        aeronave_aeroportos,
        on=["codigo_ocorrencia2", "aeronave_fase_operacao"],
        how="left",
    ).copy()

    df["ponta"] = df["aeronave_fase_operacao"].map(fase_para_ponta)

    def _pick(row: pd.Series) -> str:
        ponta = row["ponta"]
        if ponta == "aeronave_voo_destino":
            val = row["aeronave_voo_destino"]
        elif ponta == "aeronave_voo_origem":
            val = row["aeronave_voo_origem"]
        else:
            return "NAO IDENTIFICADO"
        if pd.notna(val) and str(val).strip() not in ("", "***"):
            return val
        return "NAO IDENTIFICADO"

    df["aeroporto"] = df.apply(_pick, axis=1)
    return df


def build_fase_aeroporto(
    df_com_fase: pd.DataFrame,
    df_aeronave: pd.DataFrame,
    fase_para_ponta: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Count occurrences grouped by (flight phase, ponta, airport)."""
    df = resolve_aeroporto(df_com_fase, df_aeronave, fase_para_ponta)
    return (
        df.groupby(["aeronave_fase_operacao", "ponta", "aeroporto"], dropna=False)
        .size()
        .reset_index(name="contagem")
        .sort_values(["aeronave_fase_operacao", "contagem"], ascending=[True, False])
        .reset_index(drop=True)
    )


def build_ocorrencias_por_aeroporto(
    df_com_fase: pd.DataFrame,
    df_aeronave: pd.DataFrame,
    fase_para_ponta: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Count occurrences grouped by (airport, classification), excluding
    unidentified airports."""
    df = resolve_aeroporto(df_com_fase, df_aeronave, fase_para_ponta)
    return (
        df[df["aeroporto"] != "NAO IDENTIFICADO"]
        .groupby(["aeroporto", "ocorrencia_classificacao"])
        .size()
        .reset_index(name="contagem")
        .sort_values("contagem", ascending=False)
        .reset_index(drop=True)
    )


class DataFrameOperations:
    """Loads one or more CSVs via pandas; stores the last combined result."""

    def __init__(
        self,
        sep: str = ";",
        encoding: str = "latin1",
        dataframe: pd.DataFrame | None = None,
    ) -> None:
        self._sep = sep
        self._encoding = encoding
        self._dataframe = dataframe

    @property
    def dataframe(self) -> pd.DataFrame | None:
        """Last DataFrame produced by load_dataframe (or set manually)."""
        return self._dataframe

    @dataframe.setter
    def dataframe(self, value: pd.DataFrame | None) -> None:
        self._dataframe = value

    def load_dataframe(
        self,
        *sources: str,
        sep: str | None = None,
        encoding: str | None = None,
        usecols: Any | None = None,
        **read_csv_kwargs: Any,
    ) -> pd.DataFrame:
        """
        Read one or more CSVs (URLs or local paths). Same separator/encoding apply to all.

        If more than one source is given, results are concatenated vertically in order
        (rows from the first file, then the second, etc.) with a fresh index.

        usecols: optional column subset, forwarded to pandas ``read_csv`` (names, indices,
        or a callable). If passed here, it overrides a ``usecols`` entry in ``read_csv_kwargs``.
        """
        if not sources:
            raise ValueError("At least one CSV source (URL or path) is required.")

        use_sep = self._sep if sep is None else sep
        use_enc = self._encoding if encoding is None else encoding

        csv_kwargs = dict(read_csv_kwargs)
        if usecols is not None:
            csv_kwargs["usecols"] = usecols

        frames: list[pd.DataFrame] = []
        for i, src in enumerate(sources):
            try:
                df = pd.read_csv(
                    src,
                    sep=use_sep,
                    encoding=use_enc,
                    **csv_kwargs,
                )
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    f"CSV source #{i + 1} not found: {src!r}"
                ) from e
            except pd.errors.EmptyDataError as e:
                raise pd.errors.EmptyDataError(
                    f"CSV source #{i + 1} is empty: {src!r}"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Failed to read CSV source #{i + 1} ({src!r}): {e}"
                ) from e
            frames.append(df)

        if len(frames) == 1:
            result = frames[0]
        else:
            result = pd.concat(frames, axis=0, ignore_index=True)

        self._dataframe = result
        return result
