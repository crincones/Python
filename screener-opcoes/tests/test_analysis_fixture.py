"""Pipeline de análise completo sobre o snapshot real de 17/09/2026."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from screener.analysis import AnalysisResult, analyze
from screener.data.dividends import DIVIDEND_COLUMNS
from screener.data.schema import (
    BARS_COLUMNS,
    OPTIONS_COLUMNS,
    SERIES_EXTRA_COLUMNS,
    SPREADS_COLUMNS,
)
from screener.settings import load_settings
from screener.spreads.builder import BEAR_PUT, BULL_CALL


@pytest.fixture(scope="module")
def result(fixture_options: pd.DataFrame) -> AnalysisResult:
    no_bars = pd.DataFrame(columns=list(BARS_COLUMNS))
    return analyze(
        fixture_options, pd.DataFrame(columns=DIVIDEND_COLUMNS), no_bars, load_settings()
    )


def test_output_columns_match_schema(result: AnalysisResult) -> None:
    assert list(result.series.columns) == list(OPTIONS_COLUMNS) + list(SERIES_EXTRA_COLUMNS)
    assert list(result.spreads.columns) == list(SPREADS_COLUMNS)


def test_both_strategies_found_across_underlyings(result: AnalysisResult) -> None:
    spreads = result.spreads
    assert {BULL_CALL, BEAR_PUT} <= set(spreads["strategy"])
    assert spreads["underlying"].nunique() >= 5
    assert {"PETR4", "VALE3", "BOVA11"} <= set(spreads["underlying"])


def test_pair_rules_hold_for_every_spread(result: AnalysisResult) -> None:
    s = result.spreads
    settings = load_settings()
    bull = s["strategy"] == BULL_CALL
    assert (s.loc[bull, "option_type"] == "call").all()
    assert (s.loc[~bull, "option_type"] == "put").all()
    assert (s.loc[bull, "short_strike"] > s.loc[bull, "long_strike"]).all()
    assert (s.loc[~bull, "short_strike"] < s.loc[~bull, "long_strike"]).all()
    assert (s["width"] <= settings.spreads.max_width_pct_spot * s["spot"] + 1e-9).all()


def test_legs_are_liquid_with_valid_iv(result: AnalysisResult) -> None:
    eligible = result.series[result.series["liquidity_ok"] & result.series["iv"].notna()]
    legs = set(result.spreads["long_symbol"]) | set(result.spreads["short_symbol"])
    assert legs <= set(eligible["symbol"])


def test_metric_identities(result: AnalysisResult) -> None:
    s = result.spreads
    bull = (s["strategy"] == BULL_CALL).to_numpy()
    np.testing.assert_allclose(s["debit"], s["long_ask"] - s["short_bid"])
    assert ((s["debit"] > 0) & (s["debit"] < s["width"])).all()
    np.testing.assert_allclose(s["reward_risk"], (s["width"] - s["debit"]) / s["debit"])
    np.testing.assert_allclose(
        s["breakeven"],
        np.where(bull, s["long_strike"] + s["debit"], s["long_strike"] - s["debit"]),
    )
    assert s["pop"].between(0, 1).all()
    np.testing.assert_allclose(
        s["liquidity_score"], np.minimum(s["long_liquidity_score"], s["short_liquidity_score"])
    )
    np.testing.assert_allclose(s["debit_per_lot"], s["debit"] * 100)


def test_pop_tracks_debit_to_width(result: AnalysisResult) -> None:
    # Com preços justos, POP ≈ débito/largura; correlação alta indica fórmulas coerentes.
    assert result.spreads["pop"].corr(result.spreads["debit_to_width"]) > 0.9


def test_summary_counts(result: AnalysisResult) -> None:
    summary = result.summary
    assert summary["spreads_valid"] == len(result.spreads)
    assert summary["series_total"] == len(result.series)
    assert summary["spreads_with_early_exercise_alert"] == int(
        result.spreads["early_exercise_alert"].sum()
    )
