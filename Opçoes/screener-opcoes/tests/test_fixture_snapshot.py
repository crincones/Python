"""Garante que a fixture real continua coerente com o schema e com as regras de coleta."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from screener.data import store
from screener.data.fixtures import REDACTED, export_fixture, redact_meta
from screener.data.schema import OPTIONS_COLUMNS, UNDERLYINGS_COLUMNS
from screener.universe_rules import REJECT_EXCLUDED

TZ = "America/Sao_Paulo"


def test_columns_match_schema(
    fixture_options: pd.DataFrame, fixture_underlyings: pd.DataFrame
) -> None:
    assert list(fixture_options.columns) == list(OPTIONS_COLUMNS)
    assert list(fixture_underlyings.columns) == list(UNDERLYINGS_COLUMNS)


def test_timestamps_are_in_sao_paulo(fixture_options: pd.DataFrame) -> None:
    for column in ("snapshot_time", "read_time", "expiration_time", "quote_time"):
        assert str(fixture_options[column].dt.tz) == TZ


def test_universe_uses_bova11_not_ibov11(fixture_underlyings: pd.DataFrame) -> None:
    by_name = fixture_underlyings.set_index("underlying")
    assert by_name.loc["BOVA11", "passed_filter"]
    assert not by_name.loc["IBOV11", "passed_filter"]
    assert by_name.loc["IBOV11", "reject_reason"] == REJECT_EXCLUDED
    assert fixture_underlyings["passed_filter"].sum() == 20


def test_options_only_for_approved_underlyings(
    fixture_options: pd.DataFrame, fixture_underlyings: pd.DataFrame
) -> None:
    approved = set(fixture_underlyings.loc[fixture_underlyings["passed_filter"], "underlying"])
    assert set(fixture_options["underlying"]) == approved


def test_series_respect_collection_window(
    fixture_options: pd.DataFrame, snapshot_path: Path
) -> None:
    settings = store.read_meta(snapshot_path)["settings"]
    spreads, collector = settings["spreads"], settings["collector"]
    assert (
        fixture_options["dte_business_days"]
        .between(spreads["dte_min_business_days"], spreads["dte_max_business_days"])
        .all()
    )
    moneyness = (fixture_options["strike"] / fixture_options["underlying_price"] - 1).abs()
    # Faixa aplicada sobre o spot do início da coleta; o spot da leitura variou até 0,17%.
    assert (moneyness <= collector["strike_range_pct_spot"] + 0.01).all()


def test_quotes_are_consistent(fixture_options: pd.DataFrame) -> None:
    book = fixture_options.dropna(subset=["bid", "ask"])
    assert (book["ask"] > book["bid"]).all()
    assert fixture_options["strike"].gt(0).all()
    assert set(fixture_options["option_type"]) == {"call", "put"}
    assert set(fixture_options["exercise_style"]) == {"american", "european"}
    # Na XP todas as puts são europeias.
    puts = fixture_options[fixture_options["option_type"] == "put"]
    assert (puts["exercise_style"] == "european").all()
    assert fixture_options["open_interest"].isna().all()


def test_fixture_meta_has_no_account_data(snapshot_path: Path) -> None:
    raw = (snapshot_path / "meta.json").read_text(encoding="utf-8")
    meta = store.read_meta(snapshot_path)
    assert meta["terminal"]["login"] == REDACTED
    assert meta["settings"]["mt5"]["terminal_path"] == REDACTED
    assert "Users" not in raw


def test_redact_meta_does_not_mutate_input() -> None:
    meta = {"terminal": {"login": 1, "path": "C:\\x"}, "settings": {"mt5": {"terminal_path": "a"}}}
    redacted = redact_meta(meta)
    assert redacted["terminal"]["login"] == REDACTED
    assert meta["terminal"]["login"] == 1


def test_export_fixture_refuses_to_overwrite(snapshot_path: Path, tmp_path: Path) -> None:
    source = tmp_path / "20260917_112013"
    source.mkdir()
    for f in snapshot_path.iterdir():
        (source / f.name).write_bytes(f.read_bytes())
    target = export_fixture(source, tmp_path / "fixtures")
    assert (target / "options.parquet").exists()
    with pytest.raises(FileExistsError):
        export_fixture(source, tmp_path / "fixtures")
