from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from screener.calendar_b3 import B3Calendar
from screener.data import store
from screener.data.normalize import normalize_options
from screener.data.schema import OPTIONS_COLUMNS, OPTIONS_TABLE
from screener.settings import load_settings

TZ = "America/Sao_Paulo"
SNAPSHOT_TIME = pd.Timestamp("2026-09-17 10:40:00", tz=TZ)
EXPIRATION_EPOCH = int(pd.Timestamp("2026-10-16 23:59:59", tz="UTC").timestamp())


def _raw() -> pd.DataFrame:
    # Primeira linha: valores reais da XP em 17/09/2026 (PETRI49). Segunda: série sem book.
    return pd.DataFrame(
        {
            "name": ["PETRI49", "PETRX99"],
            "basis": ["PETR4", "PETR4"],
            "description": ["PETR        PN   48,17", "PETRE       PN   40,00"],
            "option_right": [0, 1],
            "option_mode": [1, 0],
            "option_strike": [48.17, 40.0],
            "expiration_time": [EXPIRATION_EPOCH, EXPIRATION_EPOCH],
            "bid": [0.51, 0.0],
            "ask": [0.54, 0.05],
            "last": [0.53, 0.0],
            "time": [1789641290, 0],
            "session_deals": [108, 0],
            "session_volume": [272200.0, 0.0],
            "session_aw": [0.58, 0.0],
            "session_close": [0.82, 0.0],
            "session_interest": [0.0, 0.0],
            "trade_contract_size": [1.0, 1.0],
            "trade_tick_size": [0.01, 0.01],
            "underlying_bid": [48.05, 48.05],
            "underlying_ask": [48.07, 48.07],
            "underlying_last": [0.0, 0.0],
            "underlying_time": [1789641295, 1789641295],
            "read_time": [pd.Timestamp("2026-09-17 10:34:55", tz=TZ)] * 2,
        }
    )


def _normalized() -> pd.DataFrame:
    calendar = B3Calendar.from_csv(load_settings().paths.holidays_file)
    return normalize_options(_raw(), SNAPSHOT_TIME, SNAPSHOT_TIME.date(), TZ, calendar)


def test_normalize_options_derives_fields() -> None:
    frame = _normalized()
    assert list(frame.columns) == list(OPTIONS_COLUMNS)
    row = frame.iloc[0]
    assert (row["option_type"], row["exercise_style"]) == ("call", "american")
    assert row["expiration_date"] == dt.date(2026, 10, 16)
    assert row["expiration_time"] == pd.Timestamp("2026-10-16 23:59:59", tz=TZ)
    assert row["dte_business_days"] == 20
    assert row["dte_calendar_days"] == 29
    assert row["mid"] == pytest.approx(0.525)
    assert row["spread_pct_mid"] == pytest.approx(0.03 / 0.525)
    assert row["turnover_brl"] == pytest.approx(272200 * 0.58)
    assert row["quote_age_seconds"] == pytest.approx(5.0)
    assert np.isnan(row["open_interest"])
    assert row["underlying_price"] == pytest.approx(48.06)  # sem last → mid


def test_normalize_options_marks_missing_book() -> None:
    row = _normalized().iloc[1]
    assert (row["option_type"], row["exercise_style"]) == ("put", "european")
    assert np.isnan(row["bid"]) and np.isnan(row["mid"]) and np.isnan(row["spread_pct_mid"])
    assert pd.isna(row["quote_time"])
    assert row["turnover_brl"] == 0


def test_snapshot_roundtrip_keeps_timezone(tmp_path: Path) -> None:
    frame = _normalized()
    path = store.write_snapshot(tmp_path, SNAPSHOT_TIME, {OPTIONS_TABLE: frame}, {"ok": True})
    assert path.name == "20260917_104000"
    assert store.resolve_snapshot(tmp_path, "latest") == path
    loaded = store.read_table(path, OPTIONS_TABLE)
    assert str(loaded["quote_time"].dt.tz) == TZ
    assert loaded.loc[0, "quote_time"] == pd.Timestamp("2026-09-17 10:34:50", tz=TZ)
    assert loaded.loc[0, "strike"] == 48.17
    assert store.read_meta(path) == {"ok": True}


def test_partial_snapshot_is_not_resolved(tmp_path: Path) -> None:
    (tmp_path / "20260917_104000.partial").mkdir()
    with pytest.raises(store.SnapshotNotFoundError):
        store.resolve_snapshot(tmp_path, "latest")
