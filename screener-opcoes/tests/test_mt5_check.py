from __future__ import annotations

import pytest

from screener.settings import load_settings

pytestmark = pytest.mark.mt5


def test_check_against_live_terminal() -> None:
    from screener.collector.field_audit import run_check
    from screener.collector.mt5_client import MT5Client

    settings = load_settings()
    with MT5Client(settings.mt5) as client:
        report = run_check(client, settings)

    assert report.terminal["connected"]
    assert report.total_options > 0
    assert set(report.right_mode_counts["right"]) <= {"call", "put"}
    assert report.sample_size > 0
