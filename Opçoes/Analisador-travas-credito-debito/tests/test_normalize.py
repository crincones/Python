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
