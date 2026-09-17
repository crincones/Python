from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from screener.calendar_b3 import B3Calendar
from screener.settings import load_settings
from screener.universe_rules import (
    REJECT_EXCLUDED,
    REJECT_FEW_SERIES,
    REJECT_LOW_TURNOVER,
    REJECT_NO_PRICE,
    REJECT_OUT_OF_TOP,
    average_daily_turnover,
    feed_problem,
    filter_underlyings,
    select_candidate_series,
)


def _epoch(day: dt.date) -> int:
    return int(pd.Timestamp(day, tz="UTC").timestamp())


def test_average_daily_turnover_ignores_partial_bar_and_reports_gaps() -> None:
    expected = [dt.date(2026, 9, 14), dt.date(2026, 9, 15), dt.date(2026, 9, 16)]
    rates = pd.DataFrame(
        {
            "time": [
                _epoch(dt.date(2026, 9, 14)),
                _epoch(dt.date(2026, 9, 16)),
                _epoch(dt.date(2026, 9, 17)),
            ],
            "close": [10.0, 20.0, 99.0],
            "real_volume": [1000, 2000, 1],
        }
    )
    stats = average_daily_turnover(rates, expected)
    assert stats["avg_daily_turnover_brl"] == (10_000 + 40_000) / 2
    assert stats["sessions_used"] == 2
    assert stats["missing_sessions"] == [dt.date(2026, 9, 15)]


def test_average_daily_turnover_without_bars_reports_all_sessions_missing() -> None:
    expected = [dt.date(2026, 9, 15), dt.date(2026, 9, 16)]
    stats = average_daily_turnover(pd.DataFrame(), expected)
    assert stats["missing_sessions"] == expected
    assert stats["sessions_used"] == 0


def test_filter_underlyings_reasons_and_top_n() -> None:
    rules = load_settings().underlying_filter.model_copy(
        update={
            "min_listed_series": 50,
            "min_avg_daily_turnover_brl": 100e6,
            "max_underlyings": 2,
            "excluded_underlyings": ["G"],
        }
    )
    stats = pd.DataFrame(
        {
            "underlying": ["A", "B", "C", "D", "E", "F", "G"],
            "listed_series": [500, 500, 10, 500, 500, 500, 500],
            "price": [10.0, 20.0, 30.0, np.nan, 40.0, 50.0, 60.0],
            "avg_daily_turnover_brl": [900e6, 300e6, 900e6, 900e6, 50e6, 200e6, 9e12],
        }
    )
    result = filter_underlyings(stats, rules).set_index("underlying")
    assert result.loc[["A", "B"], "passed_filter"].all()
    assert result.loc["A", "liquidity_rank"] == 1
    assert result.loc["C", "reject_reason"] == REJECT_FEW_SERIES
    assert result.loc["D", "reject_reason"] == REJECT_NO_PRICE
    assert result.loc["E", "reject_reason"] == REJECT_LOW_TURNOVER
    assert result.loc["F", "reject_reason"] == REJECT_OUT_OF_TOP
    assert result.loc["G", "reject_reason"] == REJECT_EXCLUDED
    assert result["passed_filter"].sum() == 2


def test_select_candidate_series_applies_dte_window_and_strike_range() -> None:
    settings = load_settings()
    calendar = B3Calendar.from_csv(settings.paths.holidays_file)
    collector = settings.collector.model_copy(update={"strike_range_pct_spot": 0.2})
    spreads = settings.spreads.model_copy(
        update={"dte_min_business_days": 5, "dte_max_business_days": 30}
    )
    in_window = dt.date(2026, 10, 16)
    options = pd.DataFrame(
        {
            "symbol": ["IN", "TOO_SOON", "TOO_LATE", "FAR_STRIKE", "NO_SPOT"],
            "underlying": ["X", "X", "X", "X", "Y"],
            "strike": [105.0, 100.0, 100.0, 130.0, 50.0],
            "expiration_date": [
                in_window,
                dt.date(2026, 9, 18),
                dt.date(2026, 12, 18),
                in_window,
                in_window,
            ],
        }
    )
    spots = pd.Series({"X": 100.0})
    result = select_candidate_series(
        options, spots, dt.date(2026, 9, 17), calendar, collector, spreads
    )
    assert result["symbol"].tolist() == ["IN"]
    assert result["dte_business_days"].tolist() == [20]  # 12/10 é feriado


def _raw_quotes(times: list[int], underlying_bid: float = 48.0) -> pd.DataFrame:
    n = len(times)
    return pd.DataFrame(
        {
            "time": times,
            "underlying_bid": [underlying_bid] * n,
            "underlying_ask": [underlying_bid] * n,
            "underlying_last": [0.0] * n,
        }
    )


def test_feed_problem_accepts_healthy_read() -> None:
    assert feed_problem(_raw_quotes([1, 0, 0, 0]), 0.25) is None


def test_feed_problem_detects_stalled_feed() -> None:
    assert feed_problem(pd.DataFrame(), 0.05) == "nenhuma série lida"
    assert "ativo-objeto" in feed_problem(_raw_quotes([1, 1], underlying_bid=0.0), 0.05)
    assert "0.0%" in feed_problem(_raw_quotes([0, 0, 0, 0]), 0.05)
