from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


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
        **read_csv_kwargs: Any,
    ) -> pd.DataFrame:
        """
        Read one or more CSVs (URLs or local paths). Same separator/encoding apply to all.

        If more than one source is given, results are concatenated vertically in order
        (rows from the first file, then the second, etc.) with a fresh index.
        """
        if not sources:
            raise ValueError("At least one CSV source (URL or path) is required.")

        use_sep = self._sep if sep is None else sep
        use_enc = self._encoding if encoding is None else encoding

        frames: list[pd.DataFrame] = []
        for i, src in enumerate(sources):
            try:
                df = pd.read_csv(
                    src,
                    sep=use_sep,
                    encoding=use_enc,
                    **read_csv_kwargs,
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
