"""Viés automático e score sobre o snapshot real com barras (17/09/2026 12:27)."""

from __future__ import annotations

import pandas as pd
import pytest

from screener.analysis import AnalysisResult, analyze
from screener.data.dividends import DIVIDEND_COLUMNS
from screener.data.schema import BARS_COLUMNS, SPREADS_COLUMNS
from screener.settings import load_settings
from screener.signals.direction import SOURCE_AUTO, SOURCE_MANUAL

TZ = "America/Sao_Paulo"


@pytest.fixture(scope="module")
def settings():
    # Viés manual vazio: o teste valida o sinal automático sobre barras reais.
    return load_settings().model_copy(update={"bias": {}})


@pytest.fixture(scope="module")
def result(
    bars_fixture_options: pd.DataFrame, fixture_bars: pd.DataFrame, settings
) -> AnalysisResult:
    return analyze(
        bars_fixture_options, pd.DataFrame(columns=DIVIDEND_COLUMNS), fixture_bars, settings
    )


def test_bars_fixture_schema(fixture_bars: pd.DataFrame) -> None:
    assert list(fixture_bars.columns) == list(BARS_COLUMNS)
    assert set(fixture_bars["timeframe"]) == {"d1", "h4"}
    assert str(fixture_bars["time"].dt.tz) == TZ
    per_series = fixture_bars.groupby(["underlying", "timeframe"]).size()
    assert (per_series == 200).all()
    assert fixture_bars["underlying"].nunique() == 20


def test_automatic_bias_on_real_bars(result: AnalysisResult) -> None:
    bias = result.bias.set_index("underlying")
    assert (bias["bias_source"] == SOURCE_AUTO).all()
    # Leitura registrada em 17/09/2026 12:27 (regressão do sinal).
    assert bias.loc["VALE3", "bias"] == "baixa"
    assert bias.loc["BOVA11", "bias"] == "alta"
    assert bias.loc["PETR4", "bias"] == "neutro"  # D1 alta, H4 neutro
    assert bias.loc["PETR4", "d1_trend"] == "alta"
    vale = bias.loc["VALE3"]
    assert vale["d1_close"] < vale["d1_ema_slow"] and vale["d1_ema_fast"] < vale["d1_ema_slow"]


def test_ranked_spreads_are_in_band_and_aligned(result: AnalysisResult, settings) -> None:
    spreads = result.spreads
    assert list(spreads.columns) == list(SPREADS_COLUMNS)
    ranked = spreads[spreads["ranked"]]
    assert len(ranked) > 0
    assert ranked["pop"].between(settings.scoring.pop_min, settings.scoring.pop_max).all()
    assert (ranked["direction"] == ranked["bias"]).all()
    neutral = result.bias.loc[result.bias["bias"] == "neutro", "underlying"]
    assert not spreads.loc[spreads["underlying"].isin(neutral), "ranked"].any()
    for _, group in ranked.groupby("strategy"):
        ordered = group.sort_values("rank")
        assert ordered["rank"].tolist() == list(range(1, len(group) + 1))
        assert ordered["score"].is_monotonic_decreasing


def test_score_components_are_not_redundant(result: AnalysisResult) -> None:
    band = result.spreads[result.spreads["in_pop_band"]]
    assert band["score"].between(0, 100).all()
    assert abs(band["pct_liquidity"].corr(band["pct_execution_cost"])) < 0.5
    assert result.spreads.loc[~result.spreads["in_pop_band"], "score"].isna().all()


def test_manual_bias_overrides_signal(
    bars_fixture_options: pd.DataFrame, fixture_bars: pd.DataFrame, settings
) -> None:
    manual = settings.model_copy(update={"bias": {"VALE3": "alta", "BOVA11": "neutro"}})
    out = analyze(
        bars_fixture_options, pd.DataFrame(columns=DIVIDEND_COLUMNS), fixture_bars, manual
    )
    bias = out.bias.set_index("underlying")
    assert bias.loc["VALE3", ["bias", "bias_source"]].tolist() == ["alta", SOURCE_MANUAL]
    ranked = out.spreads[out.spreads["ranked"]]
    assert "BOVA11" not in set(ranked["underlying"])
    assert set(ranked.loc[ranked["underlying"] == "VALE3", "strategy"]) <= {"bull_call"}
