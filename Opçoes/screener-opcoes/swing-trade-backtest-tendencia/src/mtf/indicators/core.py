"""Indicadores vetorizados. Todos são causais: o valor na barra t usa só barras ≤ t."""

from __future__ import annotations

import pandas as pd


def moving_average(close: pd.Series, period: int, kind: str) -> pd.Series:
    if kind == "SMA":
        return close.rolling(period, min_periods=period).mean()
    if kind == "EMA":
        return close.ewm(span=period, adjust=False, min_periods=period).mean()
    raise ValueError(f"tipo de média desconhecido: {kind}")


def true_range(bars: pd.DataFrame) -> pd.Series:
    previous_close = bars["close"].shift()
    ranges = pd.concat(
        [
            bars["high"] - bars["low"],
            (bars["high"] - previous_close).abs(),
            (bars["low"] - previous_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(bars: pd.DataFrame, period: int) -> pd.Series:
    """ATR de Wilder (média exponencial com alpha = 1/period)."""
    return true_range(bars).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
