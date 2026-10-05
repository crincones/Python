"""Definições de tendência. Modelo A (média + inclinação), CLAUDE.md seção 6.

Os modelos B (estrutura HH/HL) e C (score combinado) entram nas próximas etapas da pesquisa.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mtf.config import MASettings
from mtf.indicators.core import moving_average
from mtf.models import TrendState


def ma_trend(bars: pd.DataFrame, settings: MASettings) -> pd.DataFrame:
    """Alta: close > MM e MM[t] > MM[t−n]. Baixa: espelho. Senão (ou sem histórico): neutro."""
    ma = moving_average(bars["close"], settings.ma_period, settings.ma_type)
    slope = ma - ma.shift(settings.slope_period)
    bullish = (bars["close"] > ma) & (slope > 0)
    bearish = (bars["close"] < ma) & (slope < 0)
    state = np.select(
        [bullish, bearish], [TrendState.BULLISH, TrendState.BEARISH], TrendState.NEUTRAL
    )
    return pd.DataFrame({"trend": state.astype("int8"), "ma": ma, "ma_slope": slope})
