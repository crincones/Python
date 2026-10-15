"""Retração H1 por direção (CLAUDE.md, seção 8): candles consecutivos contra a tendência."""

from __future__ import annotations

import numpy as np
import pandas as pd


def consecutive_run(mask: pd.Series) -> pd.Series:
    """Comprimento da sequência de True que termina em cada barra (0 onde mask é False)."""
    values = mask.to_numpy(dtype=bool)
    groups = np.cumsum(~values)
    counts = pd.Series(values.astype(int)).groupby(groups).cumsum()
    return pd.Series(counts.to_numpy(), index=mask.index)


def pullback_runs(h1: pd.DataFrame) -> pd.DataFrame:
    """Para cada barra: tamanho da sequência de candles de baixa (retração numa alta) e de alta
    (retração numa baixa) terminando nela, com extremos da sequência."""
    down = consecutive_run(h1["close"] < h1["open"])
    up = consecutive_run(h1["close"] > h1["open"])
    return pd.DataFrame({"run_down": down, "run_up": up})


def window_extreme(series: pd.Series, lengths: pd.Series, how: str) -> pd.Series:
    """Mínimo/máximo de `series` nas últimas `lengths[i]` barras terminando em i (0 → NaN)."""
    values = series.to_numpy(dtype=float)
    result = np.full(len(values), np.nan)
    func = np.min if how == "min" else np.max
    for i, n in enumerate(lengths.to_numpy()):
        if n > 0:
            result[i] = func(values[i - n + 1 : i + 1])
    return pd.Series(result, index=series.index)
