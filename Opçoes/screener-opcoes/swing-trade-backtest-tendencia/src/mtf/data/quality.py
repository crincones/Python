"""Verificações de qualidade dos dados (CLAUDE.md, seção 4)."""

from __future__ import annotations

import pandas as pd

from mtf.models import MarketData


def check_bars(bars: pd.DataFrame) -> dict:
    ohlc_bad = (
        (bars["high"] < bars[["open", "close"]].max(axis=1))
        | (bars["low"] > bars[["open", "close"]].min(axis=1))
        | (bars[["open", "high", "low", "close"]] <= 0).any(axis=1)
    )
    return {
        "bars": len(bars),
        "duplicates": int(bars["time"].duplicated().sum()),
        "unsorted": int((bars["time"].diff().dt.total_seconds() <= 0).sum()),
        "ohlc_inconsistent": int(ohlc_bad.sum()),
        "zero_volume": int((bars["real_volume"] <= 0).sum()),
    }


def overnight_gaps(d1: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Gaps D1 acima do limite: possível desdobramento/grupamento ou série não ajustada."""
    gap = d1["open"] / d1["close"].shift() - 1
    flagged = d1.loc[gap.abs() > threshold, ["time", "open"]].assign(
        previous_close=d1["close"].shift(), gap_pct=gap
    )
    return flagged.dropna()


def session_coverage(data: MarketData) -> dict:
    """Compara os pregões do D1 com os dias que têm barras H1 e H4."""
    d1_days = set(data.d1["time"].dt.date)
    h1_days = data.h1["time"].dt.date
    h4_days = set(data.h4["time"].dt.date)
    h1_per_day = h1_days.value_counts()
    common = d1_days & set(h1_days)
    return {
        "d1_days_without_h1": len(d1_days - set(h1_days) - {min(d1_days)}),
        "h1_days_without_d1": len(set(h1_days) - d1_days),
        "d1_days_without_h4": len(d1_days - h4_days - {min(d1_days)}),
        "h1_bars_per_day_median": float(h1_per_day.median()),
        "h1_short_days": int((h1_per_day < h1_per_day.median() - 2).sum()),
        "overlap_days": len(common),
    }


def quality_report(data: MarketData, gap_threshold: float) -> dict:
    gaps = overnight_gaps(data.d1, gap_threshold)
    report: dict = {"symbol": data.symbol}
    for tf, frame in (("d1", data.d1), ("h4", data.h4), ("h1", data.h1)):
        report.update({f"{tf}_{k}": v for k, v in check_bars(frame).items()})
    report.update(session_coverage(data))
    report["large_gaps"] = len(gaps)
    report["large_gap_dates"] = ", ".join(
        f"{row.time.date()} ({row.gap_pct:+.0%})" for row in gaps.itertuples()
    )
    return report
