from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from screener import liquidity as liq
from screener.settings import load_settings

RULES = load_settings().series_liquidity.model_copy(
    update={
        "max_spread_pct_mid": 0.10,
        "min_mid_price_brl": 0.05,
        "min_turnover_brl": 50_000,
        "min_deals": 20,
        "min_open_interest": None,
        "max_quote_age_seconds": 120,
    }
)


def _series(**overrides: list) -> pd.DataFrame:
    base = {
        "underlying": ["PETR4"],
        "bid": [1.00],
        "ask": [1.04],
        "mid": [1.02],
        "spread_pct_mid": [0.04 / 1.02],
        "turnover_brl": [100_000.0],
        "deals": [50],
        "open_interest": [np.nan],
        "quote_age_seconds": [5.0],
    }
    n = max(len(v) for v in overrides.values()) if overrides else 1
    frame = {k: (v * n if len(v) == 1 else v) for k, v in base.items()}
    frame.update(overrides)
    return pd.DataFrame(frame)


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"bid": [np.nan]}, liq.REJECT_NO_BOOK),
        ({"quote_age_seconds": [600.0]}, liq.REJECT_STALE),
        ({"quote_age_seconds": [np.nan]}, liq.REJECT_STALE),
        ({"mid": [0.03]}, liq.REJECT_LOW_PREMIUM),
        ({"spread_pct_mid": [0.25]}, liq.REJECT_WIDE_SPREAD),
        ({"turnover_brl": [10_000.0]}, liq.REJECT_LOW_TURNOVER),
        ({"deals": [3]}, liq.REJECT_FEW_DEALS),
    ],
)
def test_each_minimum_rejects(override: dict, reason: str) -> None:
    result = liq.evaluate_series_liquidity(_series(**override), RULES)
    assert not result.loc[0, "liquidity_ok"]
    assert result.loc[0, "liquidity_reject_reason"] == reason
    assert np.isnan(result.loc[0, "liquidity_score"])


def test_first_failed_minimum_is_reported() -> None:
    result = liq.evaluate_series_liquidity(_series(spread_pct_mid=[0.5], deals=[1]), RULES)
    assert result.loc[0, "liquidity_reject_reason"] == liq.REJECT_WIDE_SPREAD


def test_open_interest_filter_only_when_configured() -> None:
    with_oi = RULES.model_copy(update={"min_open_interest": 1000})
    frame = _series(open_interest=[np.nan])
    assert liq.evaluate_series_liquidity(frame, RULES).loc[0, "liquidity_ok"]
    result = liq.evaluate_series_liquidity(frame, with_oi)
    assert result.loc[0, "liquidity_reject_reason"] == liq.REJECT_LOW_OPEN_INTEREST


def test_open_interest_weight_is_redistributed_without_data() -> None:
    weights = liq.active_weights(_series(), RULES)
    assert "open_interest" not in weights
    assert sum(weights.values()) == pytest.approx(1.0)
    assert weights["spread"] == pytest.approx(0.35 / 0.90)


def test_score_ranks_within_underlying() -> None:
    frame = _series(
        underlying=["PETR4", "PETR4", "VALE3"],
        spread_pct_mid=[0.01, 0.05, 0.09],
        turnover_brl=[900_000.0, 60_000.0, 51_000.0],
        deals=[500, 21, 20],
    )
    result = liq.evaluate_series_liquidity(frame, RULES)
    assert result.loc[0, "liquidity_score"] == pytest.approx(1.0)
    assert result.loc[0, "liquidity_score"] > result.loc[1, "liquidity_score"]
    # Única série do ativo: percentil 1 em tudo, apesar de números absolutos piores.
    assert result.loc[2, "liquidity_score"] == pytest.approx(1.0)
