from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mtf.backtest.engine import _simulate_exit, run_backtest
from mtf.config import CostSettings, Variant
from mtf.models import LOCAL_TIMEZONE

BREAK = Variant(name="t", filter="pullback", trigger="break")


def _h1(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    frame["time"] = pd.date_range(
        "2024-01-02 10:00", periods=len(rows), freq="h", tz=LOCAL_TIMEZONE
    )
    return frame


def _setup(bar: int, direction: int, trigger: float, stop: float) -> pd.DataFrame:
    row = {
        "symbol": "X",
        "bar": bar,
        "time": pd.Timestamp("2024-01-02", tz=LOCAL_TIMEZONE),
        "direction": direction,
        "trigger_price": trigger,
        "stop_price": stop,
    }
    return pd.DataFrame([row])


def test_break_entry_and_target(settings):
    h1 = _h1([(10, 10.2, 9.8, 10.0), (10.1, 10.5, 10.0, 10.4), (10.4, 11.3, 10.3, 11.2)])
    (trade,) = run_backtest(h1, _setup(0, 1, 10.2, 9.8), BREAK, settings)
    assert trade.entry_price == pytest.approx(10.2)
    assert trade.target_price == pytest.approx(10.2 + 2 * 0.4)
    assert trade.exit_reason == "target"
    assert trade.r_multiple == pytest.approx(2.0)
    assert trade.mfe_r == pytest.approx(2.0)


def test_gap_above_trigger_fills_at_open(settings):
    h1 = _h1([(10, 10.2, 9.8, 10.0), (10.5, 10.6, 10.4, 10.5), (10.5, 10.6, 9.0, 9.2)])
    (trade,) = run_backtest(h1, _setup(0, 1, 10.2, 9.8), BREAK, settings)
    assert trade.entry_price == pytest.approx(10.5)
    assert trade.exit_reason == "stop"
    assert trade.r_multiple == pytest.approx(-1.0)
    assert trade.mae_r == pytest.approx(1.0)


def test_not_triggered_no_trade(settings):
    h1 = _h1([(10, 10.2, 9.8, 10.0), (10.0, 10.1, 9.9, 10.0), (10.0, 11, 9, 10)])
    assert run_backtest(h1, _setup(0, 1, 10.2, 9.8), BREAK, settings) == []


def test_stop_and_target_same_bar_is_stop():
    o, h = np.array([10.0, 10.0]), np.array([10.1, 12.0])
    lo, c = np.array([9.95, 9.0]), np.array([10.0, 10.0])
    assert _simulate_exit(1, 0, 9.9, 10.3, o, h, lo, c, 10) == (1, 9.9, "stop")


def test_gap_through_stop_exits_at_open():
    o, h = np.array([10.0, 9.5]), np.array([10.1, 9.6])
    lo, c = np.array([9.95, 9.4]), np.array([10.0, 9.5])
    assert _simulate_exit(1, 0, 9.9, 10.3, o, h, lo, c, 10) == (1, 9.5, "stop")


def test_short_mirror(settings):
    h1 = _h1([(10, 10.2, 9.8, 10.0), (9.9, 10.0, 9.7, 9.75), (9.7, 9.75, 8.9, 9.0)])
    (trade,) = run_backtest(h1, _setup(0, -1, 9.8, 10.2), BREAK, settings)
    assert trade.entry_price == pytest.approx(9.8)
    assert trade.exit_reason == "target"
    assert trade.target_price == pytest.approx(9.0)


def test_time_exit(settings):
    rows = [(10, 10.2, 9.8, 10.0)] + [(10.25, 10.3, 10.15, 10.25)] * 80
    (trade,) = run_backtest(_h1(rows), _setup(0, 1, 10.2, 9.8), BREAK, settings)
    assert trade.exit_reason == "time"
    assert trade.bars_held == settings.risk.max_holding_bars


def test_costs_reduce_r(settings):
    costs = CostSettings(fees_bps_per_side=10, slippage_ticks=1, tick_size=0.01)
    h1 = _h1([(10, 10.2, 9.8, 10.0), (10.1, 10.5, 10.0, 10.4), (10.4, 11.3, 10.3, 11.2)])
    (gross,) = run_backtest(h1, _setup(0, 1, 10.2, 9.8), BREAK, settings)
    with_costs = settings.model_copy(update={"costs": costs})
    (net,) = run_backtest(h1, _setup(0, 1, 10.2, 9.8), BREAK, with_costs)
    assert net.r_multiple < gross.r_multiple


def test_one_position_at_a_time(settings):
    rows = [(10, 10.2, 9.8, 10.0), (10.1, 10.5, 10.0, 10.4)] + [(10.4, 10.5, 10.3, 10.4)] * 5
    setups = pd.concat([_setup(0, 1, 10.2, 9.8), _setup(1, 1, 10.5, 10.0)], ignore_index=True)
    assert len(run_backtest(_h1(rows), setups, BREAK, settings)) == 1
