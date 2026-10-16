"""Totais da carteira, relatório das encerradas e exportação CSV."""

from __future__ import annotations

import csv
import datetime as dt
import io
import math

import pytest

from travas.tracking.export import LEG_HEADER, STRUCTURE_HEADER, legs_csv, structures_csv
from travas.tracking.report import closed_report, portfolio_totals, summary_stats, trade_rows


def closed(i, pnl, exit_date, risk=100.0, entry="2026-09-01", group="G", und="PETR4", **kw):
    return {
        "id": f"c{i}",
        "name": f"op{i}",
        "group": group,
        "underlying": und,
        "kind_label": kw.get("kind", "Trava de alta com débito"),
        "status": "encerrada",
        "entry_date": entry,
        "entry_flow": kw.get("flow", "debito"),
        "entry_cash_total": -risk,
        "costs_entry": 1.0,
        "max_loss": risk,
        "max_profit": 2 * risk,
        "realized_pnl": pnl,
        "exit": {"exit_date": exit_date, "reason": kw.get("reason", "zerada"), "costs_exit": 2.0},
        "legs": [],
    }


def opened(i, nat, mid, risk=50.0):
    return {
        "id": f"o{i}",
        "status": "aberta",
        "pnl_natural": nat,
        "pnl_mid": mid,
        "max_loss": risk,
        "entry_cash_total": -risk,
        "costs_entry": 0.5,
    }


# Sequência: +50, -100, -30, +80, +20  → acumulado 50, -50, -80, 0, 20
TRADES = [
    closed(1, 50.0, "2026-09-10"),
    closed(2, -100.0, "2026-09-20", flow="credito", kind="Trava de alta com crédito"),
    closed(3, -30.0, "2026-10-01", reason="vencida"),
    closed(4, 80.0, "2026-10-05", und="VALE3"),
    closed(5, 20.0, "2026-10-09", risk=40.0, und="VALE3"),
]


def test_portfolio_totals():
    t = portfolio_totals([*TRADES, opened(1, 10.0, 12.0), opened(2, -4.0, -3.0)])
    assert t["open_count"] == 2 and t["closed_count"] == 5
    assert t["open_pnl_natural"] == pytest.approx(6.0)
    assert t["open_pnl_mid"] == pytest.approx(9.0)
    assert t["realized_pnl"] == pytest.approx(20.0)
    assert t["total_natural"] == pytest.approx(26.0)
    assert t["open_max_loss"] == pytest.approx(100.0)
    assert t["costs_total"] == pytest.approx(5 * 3.0 + 2 * 0.5)


def test_totals_with_missing_quote_are_partial():
    t = portfolio_totals([opened(1, 10.0, None), opened(2, None, None)])
    assert t["open_pnl_natural"] == pytest.approx(10.0)
    assert t["open_missing_natural"] == 1
    assert t["open_pnl_mid"] is None and t["open_missing_mid"] == 2


def test_summary_stats():
    s = summary_stats(trade_rows(TRADES))
    assert s["trades"] == 5 and s["wins"] == 3 and s["losses"] == 2 and s["breakeven"] == 0
    assert s["win_rate"] == pytest.approx(0.6)
    assert s["net_pnl"] == pytest.approx(20.0)
    assert s["gross_profit"] == pytest.approx(150.0)
    assert s["gross_loss"] == pytest.approx(-130.0)
    assert s["profit_factor"] == pytest.approx(150 / 130)
    assert s["avg_win"] == pytest.approx(50.0) and s["avg_loss"] == pytest.approx(-65.0)
    assert s["payoff_ratio"] == pytest.approx(50 / 65)
    assert s["avg_trade"] == pytest.approx(4.0)
    assert s["largest_win"] == 80.0 and s["largest_loss"] == -100.0
    assert s["max_consecutive_wins"] == 2 and s["max_consecutive_losses"] == 2
    # pico 50 (10/09) → vale -80 (01/10)
    assert s["max_drawdown"] == pytest.approx(130.0)
    assert s["max_drawdown_from"] == "2026-09-10" and s["max_drawdown_to"] == "2026-10-01"
    assert s["recovery_factor"] == pytest.approx(20 / 130)
    assert s["total_risk"] == pytest.approx(440.0)
    assert s["return_on_risk"] == pytest.approx(20 / 440)
    rs = [0.5, -1.0, -0.3, 0.8, 0.5]
    mean = sum(rs) / 5
    sd = math.sqrt(sum((r - mean) ** 2 for r in rs) / 4)
    assert s["avg_r"] == pytest.approx(mean)
    assert s["sqn"] == pytest.approx(math.sqrt(5) * mean / sd)
    assert s["costs_total"] == pytest.approx(15.0)
    assert s["first_exit"] == "2026-09-10" and s["last_exit"] == "2026-10-09"


def test_no_losses_gives_no_profit_factor_and_empty_report():
    s = summary_stats(trade_rows([closed(1, 10.0, "2026-10-01")]))
    assert s["profit_factor"] is None and s["payoff_ratio"] is None and s["sqn"] is None
    empty = closed_report([])
    assert empty["stats"]["trades"] == 0 and empty["stats"]["win_rate"] is None
    assert empty["equity"] == [] and empty["monthly"] == []


def test_closed_report_filters_and_breakdowns():
    r = closed_report([*TRADES, opened(1, 1.0, 1.0)], start=dt.date(2026, 10, 1))
    assert [t["id"] for t in r["trades"]] == ["c3", "c4", "c5"]
    assert r["stats"]["net_pnl"] == pytest.approx(70.0)
    assert [p["cum"] for p in r["equity"]] == pytest.approx([-30.0, 50.0, 70.0])
    assert [p["dd"] for p in r["equity"]] == pytest.approx([-30.0, 0.0, 0.0])
    full = closed_report(TRADES)
    assert [(m["key"], m["net_pnl"]) for m in full["monthly"]] == [
        ("2026-09", -50.0),
        ("2026-10", 70.0),
    ]
    by_und = {b["key"]: b for b in full["by_underlying"]}
    assert by_und["VALE3"]["net_pnl"] == pytest.approx(100.0) and by_und["VALE3"]["win_rate"] == 1
    assert {b["label"] for b in full["by_flow"]} == {"Débito", "Crédito"}
    assert {b["label"] for b in full["by_reason"]} == {"Zerada", "Vencida (virou pó)"}
    assert full["trades"][0]["days_held"] == 9
    assert closed_report(TRADES, group="X")["stats"]["trades"] == 0


def parse(text):
    assert text.startswith("﻿")
    return list(csv.reader(io.StringIO(text[1:]), delimiter=";"))


def test_structures_csv_format():
    rec = {
        **closed(1, 65.5, "2026-10-10"),
        "units": 100,
        "entry_net_per_unit": 0.8,
        "breakevens": [30.8],
        "first_expiration": "2026-11-13",
        "notes": "linha 1\nlinha 2",
        "legs": [
            {"symbol": "TESTK30", "side": "compra", "quantity": 100, "entry_price": None},
            {"symbol": "TESTK32", "side": "venda", "quantity": 100, "entry_price": 0.25},
        ],
    }
    rows = parse(structures_csv([rec, {**opened(1, 12.345, None), "legs": [], "notes": ""}]))
    assert rows[0] == STRUCTURE_HEADER
    row = dict(zip(STRUCTURE_HEADER, rows[1], strict=True))
    assert row["Data entrada"] == "01/09/2026" and row["Data saída"] == "10/10/2026"
    assert row["Dias"] == "39" and row["Motivo saída"] == "Zerada"
    assert row["P&L realizado (R$)"] == "65,50" and row["R (P&L/perda máx.)"] == "0,655"
    assert row["Pernas"] == "C 100 TESTK30 | V 100 TESTK32 @ 0,25"
    assert row["Observações"] == "linha 1 linha 2"
    assert row["P&L aberto natural (R$)"] == ""
    open_row = dict(zip(STRUCTURE_HEADER, rows[2], strict=True))
    assert open_row["P&L aberto natural (R$)"] == "12,35" and open_row["P&L aberto mid (R$)"] == ""
    assert open_row["P&L realizado (R$)"] == ""


def test_legs_csv_one_row_per_leg():
    leg = {"option_type": "call", "expiration": "2026-11-13", "multiplier": 1.0, "quantity": 100}
    rec = {
        **closed(1, 10.0, "2026-10-10"),
        "exit": {"exit_date": "2026-10-10", "leg_prices": [1.2, 0.3], "reason": "zerada"},
        "legs": [
            {**leg, "symbol": "A", "side": "compra", "strike": 30.0,
             "exercise_style": "american", "entry_price": 0.9},
            {**leg, "symbol": "B", "side": "venda", "strike": 32.0,
             "exercise_style": "european", "entry_price": 0.1},
        ],
    }  # fmt: skip
    rows = parse(legs_csv([rec]))
    assert rows[0] == LEG_HEADER and len(rows) == 3
    a = dict(zip(LEG_HEADER, rows[1], strict=True))
    assert a["Lado"] == "Compra" and a["Strike"] == "30,00" and a["Preço saída"] == "1,2000"
    assert a["Estilo"] == "Americana" and a["Vencimento"] == "13/11/2026"
