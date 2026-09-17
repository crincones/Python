"""Relatório HTML gerado a partir do snapshot real com barras."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd
import pytest

from screener.analysis import analyze
from screener.data import store
from screener.data.dividends import DIVIDEND_COLUMNS
from screener.data.schema import ANALYSIS_META_FILE, BIAS_TABLE, SERIES_TABLE, SPREADS_TABLE
from screener.report.render import build_report_data, render_html, to_script_json, write_report
from screener.settings import load_settings

DATA_SCRIPT = re.compile(r'<script type="application/json" id="dados">(.*?)</script>', re.S)


@pytest.fixture(scope="module")
def analyzed_snapshot(
    tmp_path_factory: pytest.TempPathFactory,
    bars_snapshot_path: Path,
    bars_fixture_options: pd.DataFrame,
    fixture_bars: pd.DataFrame,
) -> Path:
    settings = load_settings().model_copy(update={"bias": {}})
    snapshot = tmp_path_factory.mktemp("snapshots") / "20260917_122706"
    shutil.copytree(bars_snapshot_path, snapshot)
    result = analyze(
        bars_fixture_options, pd.DataFrame(columns=DIVIDEND_COLUMNS), fixture_bars, settings
    )
    meta = {
        "analyzed_at": "2026-09-17T12:35:00-03:00",
        "snapshot": snapshot.name,
        **result.summary,
        "settings": settings.model_dump(mode="json"),
    }
    store.write_derived(
        snapshot,
        {SERIES_TABLE: result.series, SPREADS_TABLE: result.spreads, BIAS_TABLE: result.bias},
        ANALYSIS_META_FILE,
        meta,
    )
    return snapshot


@pytest.fixture(scope="module")
def html(analyzed_snapshot: Path, tmp_path_factory: pytest.TempPathFactory) -> str:
    path = write_report(analyzed_snapshot, tmp_path_factory.mktemp("output"))
    assert path.name == "relatorio_20260917_1227.html"
    return path.read_text(encoding="utf-8")


def _data(html: str) -> dict:
    match = DATA_SCRIPT.search(html)
    assert match is not None
    return json.loads(match.group(1))


def test_report_is_single_offline_file(html: str) -> None:
    assert '<html lang="pt-BR">' in html
    # Nenhuma tag carrega recurso externo (strings dentro do código do Plotly não contam).
    assert not re.search(r"<script\b[^>]*\bsrc=", html)
    markup = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S)
    assert not re.search(r'(?:src|href)\s*=\s*["\']https?://', markup)
    assert "<link" not in markup
    assert html.count("* plotly.js v") == 1


def test_embedded_data_matches_analysis(html: str, analyzed_snapshot: Path) -> None:
    data = _data(html)
    spreads = store.read_table(analyzed_snapshot, SPREADS_TABLE)
    in_band = spreads[spreads["in_pop_band"]]
    assert len(data["spreads"]) == len(in_band)
    assert data["counts"]["ranked"]["bull_call"] == int(
        (spreads["ranked"] & (spreads["strategy"] == "bull_call")).sum()
    )
    bias_underlyings = {row["underlying"] for row in data["bias"]}
    assert len(bias_underlyings) == 20
    assert set(spreads["underlying"]) <= bias_underlyings
    first = data["spreads"][0]
    assert first["ranked"] and first["rank"] == 1
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", first["expiration_date"])
    vale = next(b for b in data["bias"] if b["underlying"] == "VALE3")
    assert vale["bias"] == "baixa" and vale["price"] > 0


def test_every_spread_has_fields_for_payoff(html: str) -> None:
    for row in _data(html)["spreads"]:
        for field in ("long_strike", "short_strike", "width", "debit", "spot", "breakeven"):
            assert row[field] is not None


def test_script_json_escapes_closing_tags_and_rejects_nan() -> None:
    encoded = to_script_json({"texto": "</script><script>alert(1)</script>"})
    assert "</script>" not in encoded
    assert json.loads(encoded)["texto"] == "</script><script>alert(1)</script>"
    with pytest.raises(ValueError):
        to_script_json({"x": float("nan")})


def test_report_renders_without_ranked_spreads() -> None:
    empty = pd.DataFrame(
        columns=["in_pop_band", "strategy", "ranked", "score", "expiration_date", "underlying"]
    ).astype({"in_pop_band": bool, "ranked": bool})
    bias = pd.DataFrame(columns=["underlying", "bias", "bias_source"])
    underlyings = pd.DataFrame(
        columns=["underlying", "passed_filter", "price", "quote_time"]
    ).astype({"passed_filter": bool})
    data = build_report_data(
        empty, bias, underlyings, {}, pd.Timestamp("2026-09-17 12:27", tz="America/Sao_Paulo")
    )
    html = render_html(data)
    assert _data(html)["spreads"] == []
    assert _data(html)["counts"]["ranked"] == {"bull_call": 0, "bear_put": 0}
