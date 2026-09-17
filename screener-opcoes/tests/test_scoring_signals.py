from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from screener.scoring import score_spreads
from screener.settings import load_settings
from screener.signals import direction as sig

SETTINGS = load_settings()
SCORING = SETTINGS.scoring.model_copy(update={"pop_min": 0.35, "pop_max": 0.60})
SIGNALS = SETTINGS.signals


def _bias(**by_underlying: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "underlying": list(by_underlying),
            "bias": list(by_underlying.values()),
            "bias_source": ["manual"] * len(by_underlying),
        }
    )


def _spreads() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "underlying": ["PETR4", "PETR4", "PETR4", "PETR4", "VALE3"],
            "strategy": ["bull_call", "bull_call", "bull_call", "bear_put", "bull_call"],
            "direction": ["alta", "alta", "alta", "baixa", "alta"],
            "pop": [0.45, 0.50, 0.90, 0.40, 0.40],
            "execution_cost_pct_width": [0.005, 0.02, 0.001, 0.01, 0.03],
            "liquidity_score": [0.9, 0.5, 1.0, 0.7, 0.2],
            "reward_risk": [1.4, 1.1, 0.1, 1.5, 1.6],
        }
    )


def test_out_of_pop_band_gets_no_score_and_no_rank() -> None:
    result = score_spreads(_spreads(), _bias(PETR4="alta", VALE3="alta"), SCORING)
    assert not result.loc[2, "in_pop_band"]
    assert np.isnan(result.loc[2, "score"])
    assert not result.loc[2, "ranked"]


def test_percentiles_are_per_strategy_and_respect_direction() -> None:
    result = score_spreads(_spreads(), _bias(PETR4="alta", VALE3="alta"), SCORING)
    # bull_call na faixa: linhas 0, 1, 4. Linha 0 tem menor custo e maior liquidez.
    assert result.loc[0, "pct_execution_cost"] == pytest.approx(1.0)
    assert result.loc[4, "pct_execution_cost"] == pytest.approx(1 / 3)
    assert result.loc[0, "pct_liquidity"] == pytest.approx(1.0)
    assert result.loc[4, "pct_reward_risk"] == pytest.approx(1.0)
    # única bear_put na faixa: percentil 1 em tudo → score 100
    assert result.loc[3, "score"] == pytest.approx(100.0)
    expected = 100 * (0.40 * 1.0 + 0.40 * 1.0 + 0.20 * (2 / 3))
    assert result.loc[0, "score"] == pytest.approx(expected)


def test_ranking_follows_bias() -> None:
    result = score_spreads(_spreads(), _bias(PETR4="alta", VALE3="baixa"), SCORING)
    assert result["ranked"].tolist() == [True, True, False, False, False]
    assert result.loc[0, "rank"] == 1
    assert result.loc[1, "rank"] == 2
    assert pd.isna(result.loc[4, "rank"])


def test_neutral_or_missing_bias_ranks_nothing() -> None:
    result = score_spreads(_spreads(), _bias(PETR4="neutro"), SCORING)
    assert not result["ranked"].any()
    assert (result.loc[4, "bias"]) == "neutro"


def _bars(underlying: str, timeframe: str, closes: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "underlying": underlying,
            "timeframe": timeframe,
            "time": pd.date_range("2026-01-01", periods=len(closes), freq="D"),
            "close": closes,
        }
    )


N = 120
UP = np.linspace(40, 60, N)
DOWN = np.linspace(60, 40, N)


def test_timeframe_trend_directions() -> None:
    trend = SIGNALS.timeframes["d1"]
    assert sig.timeframe_trend(_bars("X", "d1", UP), trend, 60)["trend"] == sig.BULLISH
    assert sig.timeframe_trend(_bars("X", "d1", DOWN), trend, 60)["trend"] == sig.BEARISH
    short = sig.timeframe_trend(_bars("X", "d1", UP[:10]), trend, 60)
    assert short["trend"] == sig.NEUTRAL
    assert np.isnan(short["ema_slow"])


def test_timeframe_trend_is_neutral_when_price_and_emas_disagree() -> None:
    # Queda brusca: fechamento abaixo da EMA lenta, mas a EMA rápida ainda não cruzou.
    closes = np.r_[np.linspace(40, 60, N - 1), [57.5]]
    result = sig.timeframe_trend(_bars("X", "d1", closes), SIGNALS.timeframes["d1"], 60)
    assert result["close"] < result["ema_slow"] < result["ema_fast"]
    assert result["trend"] == sig.NEUTRAL


def test_automatic_bias_requires_agreement_between_timeframes() -> None:
    bars = pd.concat(
        [
            _bars("PETR4", "d1", UP),
            _bars("PETR4", "h4", UP),
            _bars("VALE3", "d1", DOWN),
            _bars("VALE3", "h4", DOWN),
            _bars("BBAS3", "d1", UP),
            _bars("BBAS3", "h4", DOWN),
        ]
    )
    auto = sig.automatic_bias(bars, SIGNALS).set_index("underlying")
    assert auto.loc["PETR4", "auto_bias"] == sig.BULLISH
    assert auto.loc["VALE3", "auto_bias"] == sig.BEARISH
    assert auto.loc["BBAS3", "auto_bias"] == sig.NEUTRAL
    assert auto.loc["BBAS3", "d1_trend"] == sig.BULLISH
    assert auto.loc["BBAS3", "h4_trend"] == sig.BEARISH


def test_manual_bias_overrides_automatic() -> None:
    auto = pd.DataFrame({"underlying": ["PETR4", "VALE3"], "auto_bias": [sig.BULLISH, sig.BEARISH]})
    resolved = sig.resolve_bias(
        ["PETR4", "VALE3", "ITUB4"], auto, {"VALE3": "neutro", "WEGE3": "alta"}, SIGNALS
    ).set_index("underlying")
    assert resolved.loc["PETR4", ["bias", "bias_source"]].tolist() == ["alta", sig.SOURCE_AUTO]
    assert resolved.loc["VALE3", ["bias", "bias_source"]].tolist() == ["neutro", sig.SOURCE_MANUAL]
    assert resolved.loc["ITUB4", ["bias", "bias_source"]].tolist() == ["neutro", sig.SOURCE_NONE]
    assert resolved.loc["WEGE3", "bias"] == "alta"


def test_disabled_signals_ignore_automatic_bias() -> None:
    disabled = SIGNALS.model_copy(update={"enabled": False})
    auto = pd.DataFrame({"underlying": ["PETR4"], "auto_bias": [sig.BULLISH]})
    resolved = sig.resolve_bias(["PETR4"], auto, {}, disabled)
    assert resolved.loc[0, "bias"] == "neutro"
    assert resolved.loc[0, "bias_source"] == sig.SOURCE_NONE
