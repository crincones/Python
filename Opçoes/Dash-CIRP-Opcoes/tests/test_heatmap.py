"""Heatmap: métricas sobre barras D1, eventos da B3 (parse) e montagem dos blocos. Sem rede/MT5."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from travas.heatmap.b3_company import _date, _fix_activity, _fix_sector, _num, parse_supplement
from travas.heatmap.build import build_items
from travas.heatmap.metrics import change, compute, historical_vol, rsi_wilder


def bars(closes, forming_last=True, volume=1000.0):
    n = len(closes)
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame(
        {
            "time": pd.date_range("2025-01-02", periods=n, freq="B", tz="America/Sao_Paulo"),
            "open": closes,
            "high": closes * 1.01,
            "low": closes * 0.99,
            "close": closes,
            "real_volume": volume,
            "forming": [False] * (n - 1) + [forming_last],
        }
    )


def test_changes_in_sessions():
    closes = np.arange(1, 301, dtype=float)  # 1..300
    m = compute(bars(closes))
    assert m["changes"]["1d"]["abs"] == pytest.approx(1.0)
    assert m["changes"]["1d"]["pct"] == pytest.approx(300 / 299 - 1)
    assert m["changes"]["1w"]["ref"] == pytest.approx(295)
    assert m["changes"]["1m"]["ref"] == pytest.approx(279)
    assert m["changes"]["1y"]["ref"] == pytest.approx(48)
    short = compute(bars(closes[:10]))
    assert short["changes"]["1y"]["pct"] is None  # histórico insuficiente: não inventa


def test_historical_vol_uses_closed_bars_only():
    rng = np.random.default_rng(1)
    rets = rng.normal(0, 0.02, 400)
    closes = 30 * np.exp(np.cumsum(rets))
    b = bars(closes)
    b.loc[b.index[-1], "close"] = closes[-2] * 1.5  # barra em formação absurda
    hv = compute(b)["hv"]
    expected = np.std(rets[-21:-1], ddof=1) * math.sqrt(252)  # 20 retornos das barras fechadas
    assert hv["20"] == pytest.approx(expected, rel=1e-6)
    assert historical_vol(pd.Series(closes[:10]), 20) is None


def test_turnover_ratio_excludes_today():
    volume = np.full(30, 1000.0)
    volume[-1] = 3000.0
    b = bars(np.full(30, 10.0))
    b["real_volume"] = volume
    m = compute(b, session_deals=1234)
    assert m["turnover_avg20"] == pytest.approx(10_000)
    assert m["turnover_today"] == pytest.approx(30_000)
    assert m["turnover_ratio"] == pytest.approx(3.0)
    assert m["deals_session"] == 1234


def test_rsi_extremes_and_change_guard():
    assert rsi_wilder(pd.Series(np.arange(1, 40, dtype=float))) == pytest.approx(100.0)
    falling = rsi_wilder(pd.Series(np.arange(40, 1, -1, dtype=float)))
    assert falling == pytest.approx(0.0, abs=1e-9)
    assert change(pd.Series([0.0, 5.0]), 1)["pct"] is None  # referência zero: sem variação


def test_technical_summary():
    t = compute(bars(np.linspace(10, 20, 260)))["technical"]
    assert t["ema_trend"] == "alta" and t["above_sma50"] and t["above_sma200"]
    assert t["rsi_label"] == "sobrecomprado"
    assert t["from_high52_pct"] <= 0 <= t["from_low52_pct"]


def test_b3_parsers():
    assert _date("21/08/2026") == "2026-08-21"
    assert _date("31/12/9999") is None and _date("01/01/1900") is None and _date("") is None
    assert _num("0,47156696000") == pytest.approx(0.47156696)
    assert _num("12.888.732.761") == pytest.approx(12_888_732_761)
    assert _fix_sector("Petróleo. Gás e Biocombustíveis") == "Petróleo, Gás e Biocombustíveis"
    assert _fix_activity("Pesquisa. lavra. refinação. Outra frase.") == (
        "Pesquisa, lavra, refinação. Outra frase."
    )


def test_parse_supplement_filters_by_isin():
    sup = {
        "totalNumberShares": "100",
        "cashDividends": [
            {
                "isinCode": "PN",
                "label": "DIVIDENDO",
                "lastDatePrior": "21/08/2026",
                "paymentDate": "21/12/2026",
                "approvedOn": "06/08/2026",
                "rate": "0,50",
            },
            {
                "isinCode": "ON",
                "label": "DIVIDENDO",
                "lastDatePrior": "21/08/2026",
                "paymentDate": "21/12/2026",
                "approvedOn": "06/08/2026",
                "rate": "0,40",
            },
            {
                "isinCode": "PN",
                "label": "JRS CAP PROPRIO",
                "lastDatePrior": "10/03/2026",
                "paymentDate": "31/12/9999",
                "approvedOn": "01/03/2026",
                "rate": "0,10",
            },
        ],
        "stockDividends": [
            {
                "isinCode": "PN",
                "label": "GRUPAMENTO",
                "lastDatePrior": "21/06/2000",
                "approvedOn": "23/05/2000",
                "factor": "0,01",
            },
        ],
    }
    out = parse_supplement(sup, "PN")
    assert [c["value"] for c in out["cash"]] == [0.5, 0.1]  # mais recente primeiro, só PN
    assert out["cash"][1]["payment_date"] is None  # data-sentinela não vira data
    assert out["stock"][0]["type"] == "GRUPAMENTO" and out["stock"][0]["factor"] == 0.01
    assert out["total_shares"] == 100


def test_build_items_excludes_index_and_estimates_cap():
    daily = {
        "PETR4": (
            bars(np.linspace(30, 40, 300)),
            {"description": "PETROBRAS PN", "session_deals": 10},
        ),
        "IBOV11": (bars(np.linspace(100, 120, 300)), {"description": "IBOV", "session_deals": 1}),
    }
    profiles = {"PETR4": {"trading_name": "PETROBRAS", "sector": "Petróleo"}}
    items = build_items(daily, profiles, {"PETR4": 1_000.0})
    assert [i["ticker"] for i in items] == ["PETR4"]
    assert items[0]["market_cap_approx"] == pytest.approx(40_000)
    assert items[0]["sector"] == "Petróleo" and items[0]["name"] == "PETROBRAS"


def test_technical_uses_configured_ema_periods():
    closes = np.linspace(10, 20, 260)
    t = compute(bars(closes), ema_periods=(17, 72))["technical"]
    assert (t["ema_fast_period"], t["ema_slow_period"]) == (17, 72)
    expected = pd.Series(closes).ewm(span=72, adjust=False).mean().iloc[-1]
    assert t["ema_slow"] == pytest.approx(expected)
