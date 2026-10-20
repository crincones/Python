"""Lista de ativos com opções (arquivo de instrumentos da B3) e mesclagem com o MT5."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from travas.data.b3_instruments import B3Instruments, summarize
from travas.data.service import merge_underlyings

TODAY = dt.date(2026, 10, 15)


def raw_b3():
    rows = [
        # ativos à vista (categoria)
        ("PETR4", "PETR4", "SHARES", None, None),
        ("SMAL11", "SMAL11", "ETF EQUITIES", None, None),
        ("IBOV11", "IBOV11", "INDEX", None, None),
        # opções vigentes
        ("PETRK1", "PETR4", "OPTION ON EQUITIES", "2026-11-19", "Call"),
        ("PETRW1", "PETR4", "OPTION ON EQUITIES", "2026-11-19", "Put"),
        ("PETRK2", "PETR4", "OPTION ON EQUITIES", "2026-12-18", "Call"),
        ("SMALK1", "SMAL11", "OPTION ON EQUITIES", "2026-11-19", "Call"),
        ("IBOVK1", "IBOV11", "OPTION ON INDEX", "2026-11-19", "Call"),
        # vencida: não conta
        ("SMALJ1", "SMAL11", "OPTION ON EQUITIES", "2026-10-09", "Call"),
    ]
    return pd.DataFrame(rows, columns=["TckrSymb", "Asst", "SctyCtgyNm", "XprtnDt", "OptnTp"])


def test_summarize_counts_alive_series_by_underlying():
    s = summarize(raw_b3(), TODAY).set_index("underlying")
    assert s.loc["PETR4", "b3_series"] == 3
    assert (s.loc["PETR4", "calls"], s.loc["PETR4", "puts"]) == (2, 1)
    assert s.loc["SMAL11", "b3_series"] == 1  # a vencida ficou fora
    assert s.loc["SMAL11", "category"] == "ETF"
    assert s.loc["IBOV11", "category"] == "Índice"
    assert s.loc["PETR4", "next_expiration"] == dt.date(2026, 11, 19)


def test_merge_marks_assets_without_mt5_options_and_sorts_by_series():
    catalog = pd.DataFrame(
        {
            "symbol": ["PETRK1", "PETRW1"],
            "underlying": ["PETR4", "PETR4"],
            "expiration_date": [dt.date(2026, 11, 19)] * 2,
        }
    )
    b3 = summarize(raw_b3(), TODAY)
    m = merge_underlyings(catalog, b3, TODAY, TODAY)
    assert m["underlying"].tolist() == ["PETR4", "IBOV11", "SMAL11"]  # 3, 1, 1 (empate: A-Z)
    by = m.set_index("underlying")
    assert by.loc["PETR4", "has_mt5_options"] and by.loc["PETR4", "listed_series"] == 3
    assert not by.loc["SMAL11", "has_mt5_options"] and by.loc["SMAL11", "mt5_series"] == 0
    # Sem o arquivo da B3: cai para a lista do MT5.
    only = merge_underlyings(catalog, None, None, TODAY)
    assert only["underlying"].tolist() == ["PETR4"] and bool(only["has_mt5_options"].iloc[0])


def test_newer_file_wins_over_older_cache(calendar, tmp_path):
    # Caso real (19/10/2026): o cache de 15/10 impedia baixar o arquivo de 16/10.
    raw = raw_b3().assign(ExrcPric="10,00", OptnStyle="EURO")
    store = B3Instruments(tmp_path, calendar)
    store._download = lambda day: raw if day == dt.date(2026, 10, 15) else None
    assert store.summary(dt.date(2026, 10, 15))[1] == dt.date(2026, 10, 15)

    newer = raw.assign(XprtnDt=raw["XprtnDt"].replace("2026-12-18", "2027-01-15"))
    fresh = B3Instruments(tmp_path, calendar)
    fresh._download = lambda day: newer if day == dt.date(2026, 10, 16) else None
    table, day = fresh.summary(dt.date(2026, 10, 19))  # segunda: hoje ainda sem arquivo
    assert day == dt.date(2026, 10, 16)
    assert (
        "2027-01-15"
        in fresh.reference(dt.date(2026, 10, 19))["expiration_date"].astype(str).tolist()
    )
    assert not (tmp_path / "instrumentos_2026-10-15.csv").exists()  # cache antigo removido
