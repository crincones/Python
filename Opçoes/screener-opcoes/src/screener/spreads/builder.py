"""Geração dos pares válidos de trava de débito."""

from __future__ import annotations

import pandas as pd

BULL_CALL = "bull_call"
BEAR_PUT = "bear_put"
DIRECTION_BY_STRATEGY = {BULL_CALL: "alta", BEAR_PUT: "baixa"}
OPTION_TYPE_BY_STRATEGY = {BULL_CALL: "call", BEAR_PUT: "put"}

PAIR_KEYS = ["underlying", "expiration_date", "option_type"]
LEG_COLUMNS = [
    "symbol",
    "strike",
    "exercise_style",
    "bid",
    "ask",
    "mid",
    "iv",
    "spread_pct_mid",
    "turnover_brl",
    "deals",
    "liquidity_score",
    "underlying_price",
]
SHARED_COLUMNS = ["snapshot_time", "dte_business_days", "t_years", "rate"]


def build_spread_pairs(series: pd.DataFrame, max_width_pct_spot: float) -> pd.DataFrame:
    """Todos os pares de trava de débito entre séries elegíveis.

    Elegível = liquidity_ok e IV válida. Pares: mesmo ativo, vencimento e tipo; alta (call):
    strike vendido > comprado; baixa (put): strike vendido < comprado; largura ≤
    max_width_pct_spot × spot (spot da perna comprada). Colunas das pernas com prefixo long_/short_.
    """
    eligible = series[series["liquidity_ok"] & series["iv"].notna()]
    legs = eligible[PAIR_KEYS + SHARED_COLUMNS + LEG_COLUMNS]
    long_legs = legs.rename(columns={c: f"long_{c}" for c in LEG_COLUMNS})
    short_legs = legs[PAIR_KEYS + LEG_COLUMNS].rename(
        columns={c: f"short_{c}" for c in LEG_COLUMNS}
    )
    pairs = long_legs.merge(short_legs, on=PAIR_KEYS)

    is_call = pairs["option_type"] == "call"
    bull = is_call & (pairs["short_strike"] > pairs["long_strike"])
    bear = ~is_call & (pairs["short_strike"] < pairs["long_strike"])
    width = (pairs["short_strike"] - pairs["long_strike"]).abs()
    within_width = width <= max_width_pct_spot * pairs["long_underlying_price"]
    pairs = pairs[(bull | bear) & within_width].copy()

    pairs["strategy"] = pairs["option_type"].map({"call": BULL_CALL, "put": BEAR_PUT})
    pairs["direction"] = pairs["strategy"].map(DIRECTION_BY_STRATEGY)
    return pairs.reset_index(drop=True)
