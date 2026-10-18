from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from travas.data.normalize import ema, normalize_bars


def test_ema_formula_and_warmup():
    close = pd.Series(np.arange(1.0, 41.0))
    out = ema(close, 17)
    assert out.iloc[:17].isna().all()
    alpha = 2 / 18
    manual = close.iloc[0]
    for x in close.iloc[1:]:
        manual = alpha * x + (1 - alpha) * manual
    assert out.iloc[-1] == pytest.approx(manual)


def test_bars_forming_and_no_fabricated_gaps():
    day = 86_400
    # Epoch do servidor = relógio de Brasília codificado como UTC; há um buraco no dia 3.
    start = pd.Timestamp("2026-10-12").tz_localize("UTC").timestamp()
    rates = pd.DataFrame(
        {
            "time": [start, start + day, start + 3 * day],
            "open": [1.0, 2.0, 3.0],
            "high": [1.5, 2.5, 3.5],
            "low": [0.5, 1.5, 2.5],
            "close": [1.2, 2.2, 3.2],
            "tick_volume": [10, 10, 10],
            "real_volume": [100, 100, 100],
        }
    )
    now = start + 3 * day + 3600  # 1 h depois da abertura da última barra
    bars = normalize_bars(rates, "d1", "America/Sao_Paulo", now)
    assert len(bars) == 3
    assert bars["forming"].tolist() == [False, False, True]
    assert str(bars["time"].iloc[0]) == "2026-10-12 00:00:00-03:00"


def _rates(times):
    n = len(times)
    return pd.DataFrame(
        {
            "time": times,
            "open": [1.0] * n,
            "high": [1.0] * n,
            "low": [1.0] * n,
            "close": [1.0] * n,
            "tick_volume": [1] * n,
            "real_volume": [1] * n,
        }
    )


def test_monthly_bar_forms_until_next_month():
    ts = [pd.Timestamp(d).tz_localize("UTC").timestamp() for d in ("2026-09-01", "2026-10-01")]
    late_oct = pd.Timestamp("2026-10-31 23:00").tz_localize("UTC").timestamp()
    nov = pd.Timestamp("2026-11-01 00:00:01").tz_localize("UTC").timestamp()
    assert normalize_bars(_rates(ts), "mn1", "America/Sao_Paulo", late_oct)["forming"].tolist() == [
        False,
        True,
    ]
    assert normalize_bars(_rates(ts), "mn1", "America/Sao_Paulo", nov)["forming"].tolist() == [
        False,
        False,
    ]


def test_hourly_bar_forming():
    t0 = pd.Timestamp("2026-10-16 10:00").tz_localize("UTC").timestamp()
    bars = normalize_bars(_rates([t0, t0 + 3600]), "h1", "America/Sao_Paulo", t0 + 3600 + 60)
    assert bars["forming"].tolist() == [False, True]
