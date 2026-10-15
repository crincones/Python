"""Descoberta de setups: tendência D1/H4 + retração H1 + referência MM D1.

Regra contra look-ahead (CLAUDE.md, seção 36): cada barra H1 é decidida no seu fechamento
(`close_time`). Valores D1/H4 vêm da última barra D1/H4 cujo `close_time` ≤ `close_time` da barra
H1. Como a barra D1 só fecha à meia-noite, durante o pregão d vale o D1 de d−1; a barra H4 das
12:00 (12h–16h) só vale a partir do fechamento da H1 das 15:00. Nenhuma coluna usa barras
futuras; o teste tests/test_lookahead.py confere isso truncando os dados.
"""

from __future__ import annotations

import zlib

import numpy as np
import pandas as pd

from mtf.config import Settings, Variant
from mtf.indicators.core import atr, moving_average
from mtf.models import MarketData
from mtf.pullback.detector import pullback_runs, window_extreme
from mtf.trend.models import ma_trend
from mtf.universe.selection import rolling_average_daily_value


def align_to_h1(h1: pd.DataFrame, higher: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Valores da última barra superior já fechada no fechamento de cada barra H1."""
    left = pd.DataFrame({"close_time": h1["close_time"], "bar": np.arange(len(h1))})
    right = higher[["close_time", *columns]].rename(columns={"close_time": "available_at"})
    merged = pd.merge_asof(
        left, right, left_on="close_time", right_on="available_at", direction="backward"
    )
    return merged.set_index("bar")[columns]


def build_features(data: MarketData, settings: Settings) -> pd.DataFrame:
    """Uma linha por barra H1 com tudo o que se sabia no fechamento dela."""
    ref, risk = settings.reference, settings.risk
    d1, h4, h1 = data.d1, data.h4, data.h1

    d1_trend = ma_trend(d1, settings.trend.d1)
    d1_cols = pd.DataFrame(
        {
            "close_time": d1["close_time"],
            "d1_trend": d1_trend["trend"],
            "d1_ma": moving_average(d1["close"], ref.ma_period, ref.ma_type),
            "atr_d1": atr(d1, ref.atr_period),
            "adv": rolling_average_daily_value(d1, settings.universe.liquidity_window),
        }
    )
    h4_trend = ma_trend(h4, settings.trend.h4)
    h4_cols = pd.DataFrame(
        {
            "close_time": h4["close_time"],
            "h4_trend": h4_trend["trend"],
            "h4_ma": moving_average(h4["close"], ref.h4_ma_period, ref.ma_type),
            "atr_h4": atr(h4, ref.atr_period),
        }
    )
    features = pd.concat(
        [
            h1.reset_index(drop=True),
            align_to_h1(h1, d1_cols, ["d1_trend", "d1_ma", "atr_d1", "adv"]),
            align_to_h1(h1, h4_cols, ["h4_trend", "h4_ma", "atr_h4"]),
            pullback_runs(h1),
        ],
        axis=1,
    )
    features["atr_h1"] = atr(h1, risk.atr_period_h1).to_numpy()
    features["d1_trend"] = features["d1_trend"].fillna(0).astype("int8")
    features["h4_trend"] = features["h4_trend"].fillna(0).astype("int8")
    aligned = (features["d1_trend"] == features["h4_trend"]) & (features["d1_trend"] != 0)
    features["direction"] = np.where(aligned, features["d1_trend"], 0).astype("int8")
    return features


def _eligible(features: pd.DataFrame, settings: Settings) -> pd.Series:
    start = pd.Timestamp(settings.data.test_start_date, tz=features["time"].dt.tz)
    required = features[["d1_ma", "atr_d1", "adv", "h4_ma", "atr_h4", "atr_h1"]].notna().all(axis=1)
    liquid = features["adv"] >= settings.universe.min_average_daily_value
    return required & liquid & (features["time"] >= start)


def _random_direction(features: pd.DataFrame, settings: Settings, symbol: str) -> pd.Series:
    seed = settings.random_benchmark.seed + zlib.crc32(symbol.encode())
    rng = np.random.default_rng(seed)
    drawn = rng.random(len(features)) < settings.random_benchmark.probability
    side = rng.choice(np.array([-1, 1], dtype="int8"), len(features))
    return pd.Series(np.where(drawn, side, 0), index=features.index)


def build_setups(
    features: pd.DataFrame, variant: Variant, settings: Settings, symbol: str
) -> pd.DataFrame:
    """Barras candidatas da variante, com preço de gatilho, stop e medidas de contexto."""
    risk, ref = settings.risk, settings.reference
    if variant.filter == "random":
        direction = _random_direction(features, settings, symbol)
    else:
        direction = features["direction"].astype(int)

    long = direction > 0
    run = pd.Series(np.where(long, features["run_down"], features["run_up"]), index=features.index)
    if variant.filter == "pullback":
        window = run
        active = (run >= settings.pullback.min_bars) & (run <= settings.pullback.max_bars)
    else:
        window = pd.Series(risk.benchmark_stop_lookback, index=features.index)
        run = pd.Series(0, index=features.index)
        active = pd.Series(True, index=features.index)
    active &= (direction != 0) & _eligible(features, settings)

    low = window_extreme(features["low"], window.where(active, 0), "min")
    high = window_extreme(features["high"], window.where(active, 0), "max")
    start = pd.Series(np.arange(len(features)), index=features.index) - window + 1

    # Impulso: extremo das `impulse_lookback` barras anteriores à retração.
    prior_high = features["high"].rolling(ref.impulse_lookback).max().shift(1)
    prior_low = features["low"].rolling(ref.impulse_lookback).min().shift(1)
    impulse_high = prior_high.reindex(start.clip(lower=0)).to_numpy()
    impulse_low = prior_low.reindex(start.clip(lower=0)).to_numpy()

    close, d1_ma, atr_d1 = features["close"], features["d1_ma"], features["atr_d1"]
    buffer = risk.stop_buffer_atr_h1 * features["atr_h1"]
    setups = pd.DataFrame(
        {
            "symbol": symbol,
            "bar": features.index,
            "time": features["time"],
            "direction": direction,
            "trigger_price": np.where(long, features["high"], features["low"]),
            "stop_price": np.where(long, low - buffer, high + buffer),
            "d1_trend": features["d1_trend"],
            "h4_trend": features["h4_trend"],
            "pullback_bars": run,
            "pullback_low": low,
            "pullback_high": high,
            "pullback_start": start,
            "impulse_size_atr_d1": (impulse_high - impulse_low) / atr_d1,
            "pullback_depth_atr_d1": np.where(long, impulse_high - low, high - impulse_low)
            / atr_d1,
            "d1_ma": d1_ma,
            "h4_ma": features["h4_ma"],
            "atr_d1": atr_d1,
            "atr_h4": features["atr_h4"],
            "atr_h1": features["atr_h1"],
            "dist_d1_ma_atr": (close - d1_ma).abs() / atr_d1,
            "signed_dist_d1_ma_atr": (close - d1_ma) / atr_d1 * direction,
            "dist_h4_ma_atr": (close - features["h4_ma"]).abs() / features["atr_h4"],
            "touch_d1_ma": np.where(long, low <= d1_ma, high >= d1_ma),
            "adv": features["adv"],
        }
    )[active]

    if variant.max_distance_atr is not None:
        setups = setups[setups["dist_d1_ma_atr"] <= variant.max_distance_atr]
    if variant.touch:
        setups = setups[setups["touch_d1_ma"]]
    return setups.reset_index(drop=True)
