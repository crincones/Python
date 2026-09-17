from __future__ import annotations

import datetime as dt

import pandas as pd

from screener.calendar_b3 import B3Calendar
from screener.settings import load_settings


def _calendar() -> B3Calendar:
    return B3Calendar.from_csv(load_settings().paths.holidays_file)


def test_sessions_until_counts_business_days_after_start_inclusive_of_end() -> None:
    cal = _calendar()
    ends = pd.Series([dt.date(2026, 9, 17), dt.date(2026, 9, 18), dt.date(2026, 9, 25)])
    # Qui 17/09 → sex 18 = 1; → sex 25 = 6 (18, 21, 22, 23, 24, 25).
    assert cal.sessions_until(dt.date(2026, 9, 17), ends).tolist() == [0, 1, 6]


def test_sessions_until_skips_holidays() -> None:
    cal = _calendar()
    # 20/11/2026 (sex) é feriado: o vencimento de novembro foi antecipado para qui 19/11.
    ends = pd.Series([dt.date(2026, 11, 23)])
    assert cal.sessions_until(dt.date(2026, 11, 19), ends).tolist() == [1]


def test_previous_sessions_skip_weekend_and_holiday() -> None:
    cal = _calendar()
    # 07/09/2026 (seg) é feriado.
    sessions = cal.previous_sessions(dt.date(2026, 9, 9), 3)
    assert sessions == [dt.date(2026, 9, 3), dt.date(2026, 9, 4), dt.date(2026, 9, 8)]


def test_previous_sessions_from_non_session_day() -> None:
    cal = _calendar()
    assert cal.previous_sessions(dt.date(2026, 9, 19), 1) == [dt.date(2026, 9, 18)]
    assert not cal.is_session(dt.date(2026, 9, 19))
