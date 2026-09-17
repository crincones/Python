from __future__ import annotations

from pathlib import Path

import pytest

from screener.data import store
from screener.data.schema import (
    BARS_COLUMNS,
    BARS_TABLE,
    OPTIONS_COLUMNS,
    OPTIONS_TABLE,
    UNDERLYINGS_COLUMNS,
    UNDERLYINGS_TABLE,
)
from screener.settings import load_settings

pytestmark = pytest.mark.mt5


def test_collect_small_universe(tmp_path: Path) -> None:
    from screener.collector.mt5_client import MT5Client
    from screener.collector.snapshot import collect_snapshot

    base = load_settings()
    settings = base.model_copy(
        update={
            "paths": base.paths.model_copy(update={"snapshots_dir": tmp_path}),
            "underlying_filter": base.underlying_filter.model_copy(update={"max_underlyings": 1}),
            "collector": base.collector.model_copy(update={"strike_range_pct_spot": 0.05}),
        }
    )
    with MT5Client(settings.mt5) as client:
        path = collect_snapshot(client, settings)

    underlyings = store.read_table(path, UNDERLYINGS_TABLE)
    options = store.read_table(path, OPTIONS_TABLE)
    assert list(underlyings.columns) == list(UNDERLYINGS_COLUMNS)
    assert list(options.columns) == list(OPTIONS_COLUMNS)
    assert underlyings["passed_filter"].sum() == 1
    assert len(options) > 0
    assert set(options["option_type"]) <= {"call", "put"}
    assert (
        options["dte_business_days"]
        .between(settings.spreads.dte_min_business_days, settings.spreads.dte_max_business_days)
        .all()
    )
    bars = store.read_table(path, BARS_TABLE)
    assert list(bars.columns) == list(BARS_COLUMNS)
    assert set(bars["timeframe"]) == set(settings.signals.timeframes)
    assert str(bars["time"].dt.tz) == "America/Sao_Paulo"
