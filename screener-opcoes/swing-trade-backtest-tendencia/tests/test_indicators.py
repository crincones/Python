from __future__ import annotations

import pandas as pd

from mtf.config import MASettings
from mtf.indicators.core import atr, moving_average
from mtf.pullback.detector import consecutive_run, window_extreme
from mtf.statistics.metrics import max_drawdown_r, summarize
from mtf.trend.models import ma_trend


def test_sma_and_ema():
    close = pd.Series([1.0, 2, 3, 4, 5])
    assert moving_average(close, 3, "SMA").iloc[-1] == 4
    assert moving_average(close, 3, "EMA").notna().sum() == 3


def test_atr_constant_range():
    bars = pd.DataFrame({"high": [11.0] * 30, "low": [9.0] * 30, "close": [10.0] * 30})
    assert atr(bars, 14).iloc[-1] == 2.0


def test_ma_trend_states():
    up = pd.DataFrame({"close": [float(i) for i in range(40)]})
    down = pd.DataFrame({"close": [float(40 - i) for i in range(40)]})
    settings = MASettings(ma_period=10, slope_period=3)
    assert ma_trend(up, settings)["trend"].iloc[-1] == 1
    assert ma_trend(down, settings)["trend"].iloc[-1] == -1
    assert ma_trend(up, settings)["trend"].iloc[5] == 0  # sem histórico


def test_consecutive_run_and_window():
    mask = pd.Series([True, True, False, True, True, True])
    assert consecutive_run(mask).tolist() == [1, 2, 0, 1, 2, 3]
    values = pd.Series([5.0, 4, 3, 6, 2, 7])
    assert window_extreme(values, pd.Series([0, 1, 2, 0, 3, 2]), "min").tolist()[4] == 2


def test_metrics():
    r = pd.Series([1.0, -1, -1, 2, -1])
    assert max_drawdown_r(r) == 2.0
    trades = pd.DataFrame(
        {
            "r_multiple": r,
            "return_pct": r / 100,
            "exit_time": pd.date_range("2024-01-01", periods=5),
            "bars_held": 3,
            "mfe_r": 1.0,
            "mae_r": 0.5,
            "exit_reason": "stop",
        }
    )
    summary = summarize(trades, [])
    assert summary["win_rate"] == 0.4
    assert summary["profit_factor"] == 1.0


def test_chart_timestamps_are_epoch_ms():
    from mtf.reports.examples import _ms, _ts_ms

    times = pd.Series(pd.to_datetime([1_700_000_000], unit="s")).dt.tz_localize("UTC")
    assert _ms(times) == [1_700_000_000_000]
    assert _ts_ms(times.iloc[0]) == 1_700_000_000_000
