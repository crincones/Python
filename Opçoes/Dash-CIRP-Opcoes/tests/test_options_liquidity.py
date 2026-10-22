"""Aba Liquidez de Opções: ranking a partir dos fechamentos da B3 já guardados e CSV."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from travas.data.options_liquidity import (
    OptionsLiquidity,
    book_quality,
    csv_filename,
    ranking_csv,
    sort_rows,
)

TODAY = dt.date(2026, 10, 20)


class FakeInstruments:
    def reference(self, today):
        return pd.DataFrame(
            {"underlying": ["AAAA3", "BBBB4"]},
            index=pd.Index(["AAAAK10", "BBBBW20"], name="symbol"),
        )

    def summary(self, today):
        table = pd.DataFrame(
            {"underlying": ["AAAA3", "BBBB4"], "b3_series": [120, 40], "category": ["Ação", "Ação"]}
        )
        return table, today


def _seed(directory, day: str, rows):
    folder = directory / day
    folder.mkdir(parents=True)
    pd.DataFrame(rows, columns=["symbol", "segment", "turnover_brl", "deals"]).to_csv(
        folder / "negocios_b3.csv", index=False
    )


def test_ranking_uses_latest_sessions_and_builds_csv(calendar, tmp_path):
    # 19/10 e 16/10 já guardados; o dia 20/10 ainda não publicado (sem rede: não há arquivo).
    _seed(tmp_path, "2026-10-16", [("AAAAK10", "EQUITY CALL", 100.0, 4)])
    _seed(tmp_path, "2026-10-19", [("BBBBW20", "EQUITY PUT", 900.0, 10), ("AAAA3", "CASH", 1e9, 1)])
    liquidity = OptionsLiquidity(tmp_path, calendar, FakeInstruments())
    liquidity._missing = {TODAY: float("inf")}  # não tenta baixar o dia de hoje
    liquidity._trades.fetch = lambda day: None
    result = liquidity.ranking(TODAY, 2)
    assert result["sessions"] == ["2026-10-16", "2026-10-19"]
    first, second = result["rows"]
    assert (first["underlying"], first["turnover_brl"], first["deals"]) == ("BBBB4", 450.0, 5.0)
    assert (second["underlying"], second["b3_series"]) == ("AAAA3", 120)
    rows = [{**r, "has_mt5_options": r["underlying"] == "BBBB4"} for r in result["rows"]]
    text = ranking_csv(result, rows)
    lines = text.lstrip("﻿").splitlines()
    assert lines[0].startswith("posicao;ticker;categoria;giro_medio_opcoes_rs_dia")
    assert lines[1] == "1;BBBB4;Ação;450;5;40;sim;;;" + ";" * 14
    assert lines[2] == "2;AAAA3;Ação;50;2;120;não;;;" + ";" * 14
    rows[0].update(book_spread=0.042, book_with_quotes=9, book_series=12)
    assert (
        ranking_csv(result, rows).splitlines()[1].startswith("1;BBBB4;Ação;450;5;40;sim;4,2;9;12;")
    )
    rows[0].update(
        ivhv_label="cara",
        ivhv_weak=None,
        ivhv_items=[{"expiration": "2026-11-19", "atm_iv": 0.412, "hv": 0.3, "ratio": 1.3733}],
    )
    line = ranking_csv(result, rows).splitlines()[1]
    assert line.endswith(";cara;;2026-11-19;41,2;30,0;1,37" + ";" * 8)
    assert csv_filename(result, 20) == "liquidez_opcoes_top20_2pregoes_2026-10-16_a_2026-10-19.csv"


def test_book_quality_near_the_money_only():
    now = pd.Timestamp("2026-10-19 16:30", tz="America/Sao_Paulo")
    rows = []
    quotes = [(9.0, 1.0, 1.1), (10.0, 0.5, 0.52), (10.5, None, None), (14.0, 0.01, 0.03)]
    for strike, bid, ask in quotes:
        mid = None if bid is None else (bid + ask) / 2
        rows.append(
            {
                "underlying": "AAAA3",
                "strike": strike,
                "mid": mid,
                "spread_pct_mid": None if mid is None else (ask - bid) / mid,
                "underlying_price": 10.0,
                "read_time": now,
            }
        )
    q = book_quality(pd.DataFrame(rows), min_mid=0.03)["AAAA3"]
    # 14,0 fica fora da faixa de ±10%; das 3 perto do dinheiro, 2 têm book.
    assert (q["book_series"], q["book_with_quotes"]) == (3, 2)
    assert q["book_spread"] == pytest.approx((0.1 / 1.05 + 0.02 / 0.51) / 2)


def test_sort_rows_defaults_and_missing_last():
    rows = [
        {"rank": 1, "underlying": "B", "deals": 5.0, "book_spread": 0.10},
        {"rank": 2, "underlying": "A", "deals": 9.0, "book_spread": None},
        {"rank": 3, "underlying": "C", "deals": 1.0, "book_spread": 0.02},
    ]
    assert [r["underlying"] for r in sort_rows(rows, "deals")] == ["A", "B", "C"]
    assert [r["underlying"] for r in sort_rows(rows, "book")] == ["C", "B", "A"]
    assert [r["underlying"] for r in sort_rows(rows, "ticker", desc=True)] == ["C", "B", "A"]
