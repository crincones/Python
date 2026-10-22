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

    def sessions_between(self, start: dt.date, end: dt.date) -> list[dt.date]:
        """Pregões em [start, end], em ordem."""
        days = np.arange(np.datetime64(start, "D"), np.datetime64(end, "D") + ONE_DAY)
        sessions = days[np.is_busday(days, holidays=self._holidays)]
        return [pd.Timestamp(d).date() for d in sessions]

    def monthly_expiration(self, year: int, month: int) -> dt.date:
        """Vencimento mensal das opções sobre ações na B3: 3ª sexta-feira do mês; se não houver
        pregão nela, o pregão anterior (ex.: 19/11/2026, com o feriado de 20/11)."""
        first = dt.date(year, month, 1)
        third_friday = first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)
        rolled = np.busday_offset(
            np.datetime64(third_friday, "D"), 0, roll="backward", holidays=self._holidays
        )
        return pd.Timestamp(rolled).date()

    def is_monthly_expiration(self, day: dt.date) -> bool:
        return day == self.monthly_expiration(day.year, day.month)

    def index_monthly_expiration(self, year: int, month: int) -> dt.date:
        """Vencimento mensal das opções sobre o Ibovespa: quarta-feira mais próxima do dia 15;
        sem pregão nela, o pregão seguinte (ex.: 18/11/2026, 16/12/2026, 13/01/2027)."""
        fifteenth = dt.date(year, month, 15)
        offset = (2 - fifteenth.weekday()) % 7  # dias até a próxima quarta (0 se já é quarta)
        wednesday = fifteenth + dt.timedelta(days=offset if offset <= 3 else offset - 7)
        rolled = np.busday_offset(
            np.datetime64(wednesday, "D"), 0, roll="forward", holidays=self._holidays
        )
        return pd.Timestamp(rolled).date()

    def is_index_monthly_expiration(self, day: dt.date) -> bool:
        return day == self.index_monthly_expiration(day.year, day.month)

    def previous_sessions(self, day: dt.date, count: int) -> list[dt.date]:
        """Os `count` pregões imediatamente anteriores a `day` (exclusivo), do mais antigo ao
        mais recente."""
        anchor = np.datetime64(day, "D")
        sessions = [
            np.busday_offset(anchor, -offset, roll="forward", holidays=self._holidays)
            for offset in range(count, 0, -1)
        ]
        return [pd.Timestamp(s).date() for s in sessions]
