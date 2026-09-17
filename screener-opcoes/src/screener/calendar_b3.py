"""Calendário de pregões da B3 (dias úteis descontando feriados de config/feriados_b3.csv)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

BUSINESS_DAYS_PER_YEAR = 252
ONE_DAY = np.timedelta64(1, "D")


class B3Calendar:
    def __init__(self, holidays: np.ndarray) -> None:
        self._holidays = np.asarray(holidays, dtype="datetime64[D]")

    @classmethod
    def from_csv(cls, path: Path) -> B3Calendar:
        frame = pd.read_csv(path, dtype={"date": str})
        return cls(frame["date"].to_numpy(dtype="datetime64[D]"))

    @property
    def last_holiday(self) -> dt.date:
        return pd.Timestamp(self._holidays.max()).date()

    def is_session(self, day: dt.date) -> bool:
        return bool(np.is_busday(np.datetime64(day, "D"), holidays=self._holidays))

    def sessions_until(self, start: dt.date, ends: pd.Series) -> pd.Series:
        """Pregões em (start, end]: no próprio dia do vencimento o resultado é 0."""
        end_days = pd.to_datetime(ends).to_numpy(dtype="datetime64[D]")
        begin = np.full(end_days.shape, np.datetime64(start, "D") + ONE_DAY)
        counts = np.busday_count(begin, end_days + ONE_DAY, holidays=self._holidays)
        return pd.Series(counts, index=ends.index, dtype="int64")

    def previous_sessions(self, day: dt.date, count: int) -> list[dt.date]:
        """Os `count` pregões imediatamente anteriores a `day` (exclusivo), do mais antigo ao
        mais recente."""
        anchor = np.datetime64(day, "D")
        sessions = [
            np.busday_offset(anchor, -offset, roll="forward", holidays=self._holidays)
            for offset in range(count, 0, -1)
        ]
        return [pd.Timestamp(s).date() for s in sessions]
