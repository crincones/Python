"""Conversão do relógio do servidor MT5."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mtf.models import LOCAL_TIMEZONE


def mt5_epoch_to_local(epoch_seconds: np.ndarray, server_timezone: str) -> pd.Series:
    """O MT5 da XP codifica o relógio de parede do servidor (Brasília) como se fosse UTC: o
    epoch é lido como horário ingênuo, localizado no fuso do servidor e convertido."""
    naive = pd.to_datetime(pd.Series(epoch_seconds, dtype="int64"), unit="s")
    return naive.dt.tz_localize(server_timezone).dt.tz_convert(LOCAL_TIMEZONE)


def now_local() -> pd.Timestamp:
    return pd.Timestamp.now(tz=LOCAL_TIMEZONE)
