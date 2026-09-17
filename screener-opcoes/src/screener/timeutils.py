"""Conversão de timestamps do servidor MT5."""

from __future__ import annotations

import numpy as np
import pandas as pd

LOCAL_TIMEZONE = "America/Sao_Paulo"


def server_epoch_to_local(epoch_seconds: pd.Series | np.ndarray, server_timezone: str) -> pd.Series:
    """Converte epoch do servidor MT5 para timestamps com timezone America/Sao_Paulo.

    O MT5 codifica o relógio de parede do servidor como se fosse UTC. Por isso o epoch é
    lido como horário ingênuo, localizado no fuso do servidor e então convertido. Zero é
    tratado como ausente (NaT).
    """
    values = pd.Series(epoch_seconds, dtype="float64")
    naive = pd.to_datetime(values.where(values > 0), unit="s")
    return naive.dt.tz_localize(server_timezone).dt.tz_convert(LOCAL_TIMEZONE)


def server_now_epoch(server_timezone: str) -> float:
    """Horário atual no mesmo formato de epoch usado pelo servidor MT5."""
    wall_clock = pd.Timestamp.now(tz=server_timezone).tz_localize(None)
    return wall_clock.tz_localize("UTC").timestamp()
