"""Indicador IV/HV (opções baratas ou caras) da aba Liquidez de Opções e histórico diário da IV."""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest
from conftest import RATE_ANNUAL, SETTINGS, SIGMA, SPOT, TODAY, synthetic_chain

from travas.data import iv_history
from travas.data.snapshots import write_snapshot
from travas.options.vol_premium import (
    atm_iv_table,
    classify,
    monthly_listings,
    vol_premium,
    weak_book,
)
from travas.settings import VolPremiumSettings

S = VolPremiumSettings()
GOOD_BOOK = {"book_series": 10, "book_with_quotes": 9, "book_spread": 0.04}


def test_atm_iv_recovers_the_chain_volatility_and_flags_monthlies(calendar):
    atm = atm_iv_table(synthetic_chain(calendar), RATE_ANNUAL, SETTINGS.pricing, calendar)
    assert list(atm["expiration_date"]) == [dt.date(2026, 11, 13), dt.date(2026, 12, 18)]
    assert atm["atm_iv"].to_numpy() == pytest.approx([SIGMA, SIGMA], abs=0.01)
    assert list(atm["monthly"]) == [False, True]  # 13/11 é semanal; 18/12 é a 3ª sexta
    assert atm["spot"].iloc[0] == SPOT


def _closes(daily_vol: float, n: int = 300) -> pd.Series:
    """Log-retornos alternando ±a: desvio-padrão amostral conhecido."""
    rets = np.resize([daily_vol, -daily_vol], n)
    return pd.Series(30 * np.exp(np.cumsum(rets)))


def _atm(ivs: list[float], underlying: str = "AAAA3") -> pd.DataFrame:
    exps = [
        dt.date(2026, 11, 19),
        dt.date(2026, 12, 18),
        dt.date(2027, 1, 15),
        dt.date(2027, 2, 19),
    ]
    return pd.DataFrame(
        {
            "underlying": underlying,
            "expiration_date": exps[: len(ivs)],
            "dte_business_days": [25, 45, 63, 87][: len(ivs)],
            "spot": 30.0,
            "atm_iv": ivs,
            "atm_strike_distance_pct": 0.01,
            "monthly": True,
        }
    )


def _listed(atm: pd.DataFrame) -> pd.DataFrame:
    return atm[["underlying", "expiration_date", "dte_business_days"]]


def test_vol_premium_classifies_the_next_three_monthlies():
    hv = 0.30
    closes = {"AAAA3": _closes(hv / math.sqrt(252))}
    atm = _atm([0.24, 0.33, 0.40, 0.50])
    out = vol_premium(atm, _listed(atm), closes, {"AAAA3": GOOD_BOOK}, S)["AAAA3"]
    items = out["ivhv_items"]
    assert len(items) == 3  # só os 3 próximos mensais
    assert [i["label"] for i in items] == ["barata", "neutra", "cara"]
    assert items[0]["hv"] == pytest.approx(hv, rel=0.02)
    assert [i["hv_window"] for i in items] == [25, 45, 63]
    assert out["ivhv"] == pytest.approx(0.24 / items[0]["hv"])
    assert out["ivhv_label"] == "barata" and out["ivhv_expiration"] == "2026-11-19"
    assert out["ivhv_weak"] is None and out["ivhv_reason"] is None


def test_monthly_without_iv_stays_in_the_list(calendar):
    closes = {"AAAA3": _closes(0.3 / math.sqrt(252))}
    atm = _atm([0.24, 0.33, 0.40])
    no_first = atm.iloc[1:]  # 1º mensal sem IV ATM (book sem bid/ask)
    out = vol_premium(no_first, _listed(atm), closes, {"AAAA3": GOOD_BOOK}, S)["AAAA3"]
    assert out["ivhv_items"][0]["atm_iv"] is None and out["ivhv_items"][0]["label"] is None
    assert out["ivhv_expiration"] == "2026-12-18" and out["ivhv_label"] == "neutra"
    empty = atm.iloc[:0]
    out = vol_premium(empty, _listed(atm), closes, {}, S)["AAAA3"]
    assert out["ivhv"] is None and "sem IV ATM" in out["ivhv_reason"]
    # Na cadeia sintética, só 18/12 é mensal (13/11 é semanal).
    listed = monthly_listings(synthetic_chain(calendar), calendar)
    assert list(listed["expiration_date"]) == [dt.date(2026, 12, 18)]


def test_vol_premium_without_history_or_with_a_weak_book():
    atm = _atm([0.3])
    out = vol_premium(atm, _listed(atm), {}, {}, S, "MT5 desconectado")["AAAA3"]
    assert out["ivhv"] is None and out["ivhv_reason"] == "MT5 desconectado"
    short = {"AAAA3": _closes(0.02, n=10)}  # 9 retornos < janela de 25
    out = vol_premium(atm, _listed(atm), short, {"AAAA3": GOOD_BOOK}, S)["AAAA3"]
    assert "fechamentos" in out["ivhv_reason"]
    assert vol_premium(atm, _listed(atm).iloc[:0], {}, {}, S) == {}  # sem mensal listado
    assert weak_book(GOOD_BOOK, S) is None
    assert "spread mediano de 25%" in weak_book({**GOOD_BOOK, "book_spread": 0.25}, S)
    assert "só 2 séries" in weak_book({**GOOD_BOOK, "book_with_quotes": 2}, S)
    assert weak_book(None, S) is not None


def test_classify_limits():
    assert classify(None, S) is None
    assert classify(0.89, S) == "barata" and classify(0.9, S) == "neutra"
    assert classify(1.2, S) == "neutra" and classify(1.21, S) == "cara"
    with pytest.raises(ValueError):
        VolPremiumSettings(cheap_below=1.3, expensive_above=1.2)


def test_iv_history_records_each_snapshot_and_rebuilds(calendar, tmp_path):
    chain = synthetic_chain(calendar).assign(captured_at=pd.Timestamp("2026-10-14 11:00-03:00"))
    pricing = SETTINGS.pricing
    n = iv_history.record(tmp_path, chain, TODAY, "1100", RATE_ANNUAL, pricing, calendar)
    assert n == 2
    iv_history.record(tmp_path, chain, TODAY, "1100", RATE_ANNUAL, pricing, calendar)  # regrava
    table = iv_history.read_history(tmp_path / iv_history.IV_FILE)
    assert len(table) == 2 and set(table["slot"]) == {"1100"}
    assert table["atm_iv"].to_numpy() == pytest.approx([SIGMA, SIGMA], abs=0.01)
    # Rebuild a partir dos snapshots guardados (dois horários).
    for slot in ("1100", "1630"):
        write_snapshot(tmp_path, TODAY, slot, chain, {"status": "completo"})
    assert iv_history.rebuild(tmp_path, RATE_ANNUAL, pricing, calendar) == 4
    table = iv_history.read_history(tmp_path / iv_history.IV_FILE)
    assert list(table["slot"].unique()) == ["1100", "1630"]
