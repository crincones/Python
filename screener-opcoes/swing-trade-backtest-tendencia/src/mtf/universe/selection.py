"""Seleção do universo por liquidez (volume financeiro = close × real_volume)."""

from __future__ import annotations

import pandas as pd


def daily_value(d1: pd.DataFrame) -> pd.Series:
    return d1["close"] * d1["real_volume"]


def rolling_average_daily_value(d1: pd.DataFrame, window: int) -> pd.Series:
    """Média móvel do volume financeiro, alinhada à barra D1 (inclui a própria barra)."""
    return daily_value(d1).rolling(window, min_periods=window).mean()


def average_daily_value(d1: pd.DataFrame, window: int) -> float:
    """Média das últimas `window` barras D1 fechadas; NaN se não houver barras suficientes."""
    if len(d1) < window:
        return float("nan")
    return float(daily_value(d1).iloc[-window:].mean())


def rank_universe(stocks: pd.DataFrame, adv: dict[str, float], minimum: float) -> pd.DataFrame:
    """Ações com opções ordenadas pela liquidez atual; `eligible` = média acima do mínimo.

    Atenção: escolher o universo pela liquidez de HOJE introduz viés de sobrevivência. No
    backtest, o filtro de liquidez também é aplicado ponto a ponto (média até a véspera).
    """
    frame = stocks.assign(average_daily_value=stocks["symbol"].map(adv))
    frame["eligible"] = frame["average_daily_value"] >= minimum
    return frame.sort_values("average_daily_value", ascending=False).reset_index(drop=True)


def history_summary(symbol: str, bars: dict[str, pd.DataFrame], min_years: float) -> dict:
    """Registro por ativo (seção 3): período disponível e número de barras por timeframe."""
    d1 = bars["D1"]
    first, last = d1["time"].iloc[0], d1["time"].iloc[-1]
    years = (last - first).days / 365.25
    return {
        "symbol": symbol,
        "first_available_date": first.date(),
        "last_available_date": last.date(),
        "history_years": round(years, 2),
        "history_limited": years < min_years,
        **{f"bars_{tf.lower()}": len(frame) for tf, frame in bars.items()},
    }
