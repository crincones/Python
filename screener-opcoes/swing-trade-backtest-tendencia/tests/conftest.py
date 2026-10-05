from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mtf.config import load_settings
from mtf.models import BAR_COLUMNS, LOCAL_TIMEZONE, TIMEFRAME_DELTA, MarketData

H1_HOURS = range(10, 18)  # 10:00 … 17:00, como no MT5 da XP


def _aggregate(h1: pd.DataFrame, key: pd.Series, timeframe: str) -> pd.DataFrame:
    grouped = h1.groupby(key)
    bars = pd.DataFrame(
        {
            "time": grouped["time"].first().index,
            "open": grouped["open"].first().to_numpy(),
            "high": grouped["high"].max().to_numpy(),
            "low": grouped["low"].min().to_numpy(),
            "close": grouped["close"].last().to_numpy(),
            "tick_volume": grouped["tick_volume"].sum().to_numpy(),
            "real_volume": grouped["real_volume"].sum().to_numpy(),
        }
    )
    bars["close_time"] = bars["time"] + TIMEFRAME_DELTA[timeframe]
    return bars[list(BAR_COLUMNS)]


def synthetic_market(days: int = 400, seed: int = 1, symbol: str = "TEST3") -> MarketData:
    """Passeio aleatório com tendências alternadas; D1/H4 agregados do H1 como no MT5
    (H4 alinhado em 08:00/12:00/16:00)."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2021-01-04", periods=days)
    times = [pd.Timestamp(d) + pd.Timedelta(hours=h) for d in dates for h in H1_HOURS]
    n = len(times)
    drift = np.repeat(rng.choice([-0.0006, 0.0006], n // 240 + 1), 240)[:n]
    returns = drift + rng.normal(0, 0.006, n)
    close = 30 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[30.0], close[:-1]]) * (1 + rng.normal(0, 0.001, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.002, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.002, n)))
    h1 = pd.DataFrame(
        {
            "time": pd.DatetimeIndex(times).tz_localize(LOCAL_TIMEZONE),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": 1000,
            "real_volume": 1_000_000,
        }
    )
    h1["close_time"] = h1["time"] + TIMEFRAME_DELTA["H1"]
    h1 = h1[list(BAR_COLUMNS)]
    day = h1["time"].dt.normalize()
    h4_key = day + pd.to_timedelta((h1["time"].dt.hour // 4) * 4, unit="h")
    return MarketData(
        symbol=symbol,
        d1=_aggregate(h1, day, "D1"),
        h4=_aggregate(h1, h4_key, "H4"),
        h1=h1,
    )


@pytest.fixture
def settings():
    s = load_settings()
    data = s.data.model_copy(update={"test_start_date": pd.Timestamp("2021-04-01").date()})
    return s.model_copy(update={"data": data})


@pytest.fixture
def market() -> MarketData:
    return synthetic_market()
