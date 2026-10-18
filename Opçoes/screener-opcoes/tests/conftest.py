from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from screener.data import store
from screener.data.schema import BARS_TABLE, OPTIONS_TABLE, UNDERLYINGS_TABLE

FIXTURES_DIR = Path(__file__).parent / "fixtures"
# Snapshot real da XP, pregão de 17/09/2026 às 11:20 (20 ativos-objeto, 10.954 séries).
SNAPSHOT_20260917 = FIXTURES_DIR / "snapshot_20260917_112013"
# Mesmo pregão às 12:27, com barras D1/H4 (200 por timeframe) para o sinal automático.
SNAPSHOT_20260917_BARS = FIXTURES_DIR / "snapshot_20260917_122706"


@pytest.fixture(scope="session")
def snapshot_path() -> Path:
    return SNAPSHOT_20260917


@pytest.fixture(scope="session")
def fixture_options(snapshot_path: Path) -> pd.DataFrame:
    return store.read_table(snapshot_path, OPTIONS_TABLE)


@pytest.fixture(scope="session")
def fixture_underlyings(snapshot_path: Path) -> pd.DataFrame:
    return store.read_table(snapshot_path, UNDERLYINGS_TABLE)


@pytest.fixture(scope="session")
def bars_snapshot_path() -> Path:
    return SNAPSHOT_20260917_BARS


@pytest.fixture(scope="session")
def bars_fixture_options(bars_snapshot_path: Path) -> pd.DataFrame:
    return store.read_table(bars_snapshot_path, OPTIONS_TABLE)


@pytest.fixture(scope="session")
def fixture_bars(bars_snapshot_path: Path) -> pd.DataFrame:
    return store.read_table(bars_snapshot_path, BARS_TABLE)
