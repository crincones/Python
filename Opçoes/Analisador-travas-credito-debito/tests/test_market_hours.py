from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest
from conftest import synthetic_chain

from travas.data.quote_store import QuoteStore
from travas.market_hours import CLOSED, NO_SESSION, OPEN, PRE_OPEN, market_status

OPEN_T, CLOSE_T = dt.time(10, 0), dt.time(17, 55)


@pytest.mark.parametrize(
    ("when", "phase"),
    [
        (dt.datetime(2026, 10, 14, 9, 59), PRE_OPEN),  # quarta antes da abertura
        (dt.datetime(2026, 10, 14, 10, 0), OPEN),
        (dt.datetime(2026, 10, 14, 17, 54), OPEN),
        (dt.datetime(2026, 10, 14, 17, 55), CLOSED),
        (dt.datetime(2026, 10, 14, 22, 0), CLOSED),
        (dt.datetime(2026, 10, 17, 12, 0), NO_SESSION),  # sábado
        (dt.datetime(2026, 10, 12, 12, 0), NO_SESSION),  # feriado (N. Sra. Aparecida)
    ],
)
def test_market_phase(calendar, when, phase):
    status = market_status(when, calendar, OPEN_T, CLOSE_T)
    assert status.phase == phase
    assert status.is_open is (phase == OPEN)


def test_quote_store_merges_and_recomputes_terms(calendar, tmp_path):
    store = QuoteStore(tmp_path)
    chain = synthetic_chain(calendar)
    first = pd.Timestamp("2026-10-14 15:00", tz="America/Sao_Paulo")
    store.save("TEST3", chain, first)
    # Segunda captura só de uma série, com preço novo: ela prevalece; as demais continuam.
    sym = chain["symbol"].iloc[0]
    later = pd.Timestamp("2026-10-14 17:30", tz="America/Sao_Paulo")
    store.save("TEST3", chain[chain["symbol"] == sym].assign(bid=9.99), later)

    loaded = store.load("TEST3", dt.date(2026, 10, 15), calendar)
    assert len(loaded) == len(chain)
    row = loaded.set_index("symbol").loc[sym]
    assert row["bid"] == 9.99 and row["captured_at"] == later
    # Prazo recalculado a partir do dia seguinte: um pregão a menos.
    original = chain.set_index("symbol").loc[sym, "dte_business_days"]
    assert row["dte_business_days"] == original - 1
    price, captured = store.spot("TEST3")
    assert price == pytest.approx(31.0) and captured == later


def test_quote_store_drops_expired_and_missing(calendar, tmp_path):
    store = QuoteStore(tmp_path)
    assert store.load("NADA3", dt.date(2026, 10, 15), calendar) is None
    assert store.spot("NADA3") == (None, None)
    store.save("TEST3", synthetic_chain(calendar), pd.Timestamp("2026-10-14 15:00"))
    after_all = store.load("TEST3", dt.date(2027, 1, 4), calendar)
    assert after_all is None  # todos os vencimentos já passaram
