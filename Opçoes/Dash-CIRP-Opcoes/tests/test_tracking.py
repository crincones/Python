"""Carteira: cadastro, preço de entrada (líquido x pernas), P&L, encerramento e grupos."""

from __future__ import annotations

import datetime as dt

import pytest
from conftest import SETTINGS, SPOT, TODAY, synthetic_chain
from pydantic import ValidationError

from travas.options import pricing
from travas.options.liquidity import LiquidityRules, evaluate_liquidity
from travas.options.models import Flow, Side
from travas.tracking.evaluate import (
    PositionError,
    build_record,
    close_record,
    combined_record,
    entry_prices,
    evaluate_position,
    group_summaries,
)
from travas.tracking.models import ExitIn, LegIn, PositionIn
from travas.tracking.store import TrackingStore

EXP = dt.date(2026, 11, 13)
RATE_ANNUAL = 0.14
RATE = float(pricing.continuous_rate(RATE_ANNUAL))


@pytest.fixture
def chain(calendar):
    c = synthetic_chain(calendar)
    c = c.join(
        evaluate_liquidity(
            c, LiquidityRules(**{**SETTINGS.liquidity.model_dump(), "min_turnover_brl": 0})
        )
    )
    from travas.options.implied_vol import options_implied_vol

    c = c.join(options_implied_vol(c, RATE_ANNUAL, SETTINGS.pricing))
    return c.set_index("symbol", drop=False)


@pytest.fixture
def catalog(chain):
    return (
        chain[
            ["symbol", "underlying", "option_type", "exercise_style", "strike", "expiration_date"]
        ]
        .assign(contract_size=1.0)
        .reset_index(drop=True)
    )


def sym(chain, kind, strike, exp=EXP):
    rows = chain[
        (chain.option_type == kind) & (chain.strike == strike) & (chain.expiration_date == exp)
    ]
    return rows.symbol.iloc[0]


def bull_call(chain, **kw):
    legs = kw.pop(
        "legs",
        [
            LegIn(symbol=sym(chain, "call", 30), side=Side.LONG, quantity=100),
            LegIn(symbol=sym(chain, "call", 32), side=Side.SHORT, quantity=100),
        ],
    )
    defaults = dict(
        name="Alta PETR",
        group="Novembro",
        underlying="TEST3",
        legs=legs,
        entry_net=0.80,
        entry_flow=Flow.DEBIT,
        entry_date=TODAY,
    )
    defaults.update(kw)
    return PositionIn(**defaults)


def evaluate(record, chain, **kw):
    return evaluate_position(
        record,
        chain,
        SPOT,
        TODAY,
        kw.pop("calendar"),
        RATE,
        RATE_ANNUAL,
        SETTINGS.early_exercise,
        with_simulation=True,
        **kw,
    )


def test_net_price_only_gives_correct_totals(chain, catalog, calendar):
    rec = {**build_record(bull_call(chain), catalog), "id": "x", "status": "aberta"}
    assert rec["kind_label"] == "Trava de alta com débito (calls)"
    ev = evaluate(rec, chain, calendar=calendar)
    long_q, short_q = chain.loc[rec["legs"][0]["symbol"]], chain.loc[rec["legs"][1]["symbol"]]
    value_natural = (long_q["bid"] - short_q["ask"]) * 100
    assert ev["entry_cash_total"] == pytest.approx(-80.0)
    assert ev["pnl_natural"] == pytest.approx(value_natural - 80.0)
    assert ev["pnl_mid"] == pytest.approx((long_q["mid"] - short_q["mid"]) * 100 - 80.0)
    assert ev["max_loss"] == pytest.approx(80.0)
    assert ev["max_profit"] == pytest.approx(120.0)
    assert ev["breakevens"] == pytest.approx([30.80])
    assert ev["entry_mode"] == "liquido"
    assert all(leg["pnl_natural"] is None for leg in ev["legs"])  # sem preço por perna
    assert ev["simulation"]["model_available"]


def test_leg_prices_give_leg_pnl_and_flag_mismatch(chain, catalog, calendar):
    legs = [
        LegIn(symbol=sym(chain, "call", 30), side=Side.LONG, quantity=100, entry_price=1.50),
        LegIn(symbol=sym(chain, "call", 32), side=Side.SHORT, quantity=100, entry_price=0.70),
    ]
    rec = {
        **build_record(bull_call(chain, legs=legs, entry_net=0.90), catalog),
        "id": "x",
        "status": "aberta",
    }
    prices, mode, warnings = entry_prices(rec)
    assert mode == "pernas" and prices == [1.50, 0.70]
    assert warnings and "difere" in warnings[0]
    ev = evaluate(rec, chain, calendar=calendar)
    assert sum(leg["pnl_natural"] for leg in ev["legs"]) == pytest.approx(ev["pnl_natural"])


def test_costs_reduce_pnl(chain, catalog, calendar):
    base = {**build_record(bull_call(chain), catalog), "id": "a", "status": "aberta"}
    costly = {**base, "costs_entry": 10.0}
    assert evaluate(costly, chain, calendar=calendar)["pnl_natural"] == pytest.approx(
        evaluate(base, chain, calendar=calendar)["pnl_natural"] - 10
    )


def test_credit_structure_signs(chain, catalog, calendar):
    legs = [
        LegIn(symbol=sym(chain, "put", 30), side=Side.LONG, quantity=100),
        LegIn(symbol=sym(chain, "put", 32), side=Side.SHORT, quantity=100),
    ]
    rec = {
        **build_record(
            bull_call(chain, legs=legs, entry_net=0.85, entry_flow=Flow.CREDIT), catalog
        ),
        "id": "c",
        "status": "aberta",
    }
    ev = evaluate(rec, chain, calendar=calendar)
    assert ev["kind_label"] == "Trava de alta com crédito (puts)"
    assert ev["entry_cash_total"] == pytest.approx(85.0)
    assert ev["max_profit"] == pytest.approx(85.0)
    assert ev["max_loss"] == pytest.approx(115.0)
    long_q, short_q = chain.loc[legs[0].symbol], chain.loc[legs[1].symbol]
    assert ev["pnl_natural"] == pytest.approx((long_q["bid"] - short_q["ask"]) * 100 + 85.0)


def test_calendar_structure_supported(chain, catalog, calendar):
    later = dt.date(2026, 12, 18)
    legs = [
        LegIn(symbol=sym(chain, "call", 31, later), side=Side.LONG, quantity=100, entry_price=1.9),
        LegIn(symbol=sym(chain, "call", 31), side=Side.SHORT, quantity=100, entry_price=1.2),
    ]
    rec = {
        **build_record(bull_call(chain, legs=legs, entry_net=None, entry_flow=None), catalog),
        "id": "k",
        "status": "aberta",
    }
    assert rec["kind_label"] == "Calendário"
    ev = evaluate(rec, chain, calendar=calendar)
    sim = ev["simulation"]
    assert sim["multi_expiry"] and sim["available"]
    assert ev["profile_exact"] is False
    assert ev["first_expiration"] == EXP.isoformat()


def test_ratio_requires_leg_prices(chain):
    with pytest.raises(ValidationError, match="quantidades diferentes"):
        bull_call(
            chain,
            legs=[
                LegIn(symbol=sym(chain, "call", 30), side=Side.LONG, quantity=100),
                LegIn(symbol=sym(chain, "call", 32), side=Side.SHORT, quantity=200),
            ],
        )


def test_entry_price_required(chain):
    with pytest.raises(ValidationError, match="preço"):
        bull_call(chain, entry_net=None, entry_flow=None)


def test_unknown_symbol_and_wrong_underlying(chain, catalog):
    bad = bull_call(chain, legs=[LegIn(symbol="XXXX99", side=Side.LONG, quantity=100)])
    with pytest.raises(PositionError, match="não encontrado"):
        build_record(bad, catalog)
    wrong = bull_call(chain, underlying="VALE3")
    with pytest.raises(PositionError, match="não de VALE3"):
        build_record(wrong, catalog)


def test_missing_quote_makes_pnl_unavailable(chain, catalog, calendar):
    rec = {**build_record(bull_call(chain), catalog), "id": "x", "status": "aberta"}
    partial = chain.drop(index=rec["legs"][1]["symbol"])
    ev = evaluate(rec, partial, calendar=calendar)
    assert ev["pnl_natural"] is None
    assert any("cotação" in a for a in ev["alerts"])


def test_take_profit_and_stop_alerts(chain, catalog, calendar):
    rec = {
        **build_record(bull_call(chain, take_profit_pct=1), catalog),
        "id": "x",
        "status": "aberta",
    }
    rec_cheap = {**rec, "entry_net": 0.01}  # P&L muito positivo → alvo
    assert any("ALVO" in a for a in evaluate(rec_cheap, chain, calendar=calendar)["alerts"])
    rec_stop = {**rec, "entry_net": 1.90, "stop_loss_brl": 50}
    assert any("STOP" in a for a in evaluate(rec_stop, chain, calendar=calendar)["alerts"])


def test_close_and_realized(chain, catalog, calendar):
    rec = {**build_record(bull_call(chain), catalog), "id": "x", "status": "aberta"}
    exit_in = ExitIn(exit_date=TODAY, exit_net=1.50, exit_flow=Flow.CREDIT, costs_exit=5)
    closed = {**rec, **close_record(rec, exit_in)}
    ev = evaluate(closed, chain, calendar=calendar)
    assert ev["status"] == "encerrada"
    assert ev["realized_pnl"] == pytest.approx(150 - 80 - 5)
    assert ev["alerts"] == []
    by_legs = ExitIn(exit_date=TODAY, leg_prices=[2.0, 0.4])
    closed2 = {**rec, **close_record(rec, by_legs)}
    assert evaluate(closed2, chain, calendar=calendar)["realized_pnl"] == pytest.approx(
        (2.0 - 0.4) * 100 - 80
    )


def test_groups_and_combined(chain, catalog, calendar):
    a = {**build_record(bull_call(chain), catalog), "id": "a", "status": "aberta"}
    put_legs = [
        LegIn(symbol=sym(chain, "put", 30), side=Side.LONG, quantity=100),
        LegIn(symbol=sym(chain, "put", 32), side=Side.SHORT, quantity=100),
    ]
    b = {
        **build_record(
            bull_call(chain, legs=put_legs, entry_net=0.85, entry_flow=Flow.CREDIT), catalog
        ),
        "id": "b",
        "status": "aberta",
    }
    evs = [evaluate(r, chain, calendar=calendar) for r in (a, b)]
    (g,) = group_summaries(evs)
    assert g["group"] == "Novembro" and g["open"] == 2 and g["combinable"]
    assert g["pnl_natural"] == pytest.approx(evs[0]["pnl_natural"] + evs[1]["pnl_natural"])
    combo = evaluate(combined_record([a, b]), chain, calendar=calendar)
    assert combo["entry_cash_total"] == pytest.approx(-80 + 85)
    assert combo["pnl_natural"] == pytest.approx(g["pnl_natural"])
    assert combo["entry_mode"] == "agregado"
    assert len(combo["legs"]) == 4


def test_store_roundtrip(tmp_path):
    store = TrackingStore(tmp_path / "a.json")
    rec = store.add({"name": "x", "legs": []})
    assert store.get(rec["id"])["status"] == "aberta"
    store.update(rec["id"], {"status": "encerrada"})
    assert store.list()[0]["status"] == "encerrada"
    store.add({"name": "y", "legs": []})
    assert (tmp_path / "a.bak").exists()
    store.delete(rec["id"])
    assert [p["name"] for p in store.list()] == ["y"]
    with pytest.raises(KeyError):
        store.delete("nada")


def test_stop_info_feeds_the_stop_alert(chain, catalog, calendar):
    from travas.alerts.stop_watch import watch_entry

    cheap = {**build_record(bull_call(chain), catalog), "id": "x", "status": "aberta"}
    stop = evaluate(cheap, chain, calendar=calendar)["stop"]
    assert not stop["available"] and "não se aplica" in stop["reason"]  # perda 0,80 < lucro 1,20
    rec = {
        **build_record(bull_call(chain, entry_net=1.40), catalog),
        "id": "y",
        "status": "aberta",
        "stop_alert": {"enabled": True, "armed_at": "t"},
    }
    ev = evaluate(rec, chain, calendar=calendar)
    stop = ev["stop"]
    # Débito 1,40, lucro máx. 0,60: stop com a trava valendo 0,80 → no vencimento 30 + 0,80.
    assert stop["available"] and stop["expiry_price"] == pytest.approx(30.8, abs=1e-6)
    assert stop["pnl_total"] == pytest.approx(-60.0)
    assert stop["by_date"][TODAY.isoformat()] == pytest.approx(stop["today_price"])
    assert ev["stop_alert"] == {"enabled": True, "armed_at": "t"}
    entry = watch_entry(ev, "t")
    assert entry["down"] and entry["by_date"][ev["first_expiration"]] == pytest.approx(30.8)


def test_natural_exit_beyond_payoff_limits_is_omitted(chain, catalog, calendar):
    rec = {**build_record(bull_call(chain), catalog), "id": "x", "status": "aberta"}
    short = rec["legs"][1]["symbol"]
    absurd = chain.copy()
    absurd.loc[short, ["ask", "px_buy"]] = 8.00  # oferta de leilão: travas de 2,00 de largura
    ev = evaluate(rec, absurd, calendar=calendar)
    assert ev["pnl_natural"] is None and ev["pnl_pct_of_risk"] is None
    assert any("fora do limite teórico" in a for a in ev["alerts"])
    assert ev["max_loss"] == pytest.approx(80.0)  # o risco no vencimento não muda
    # Dentro do limite (book normal): o P&L natural continua exibido.
    assert evaluate(rec, chain, calendar=calendar)["pnl_natural"] is not None


def test_exit_plan_in_evaluation(chain, catalog, calendar):
    rec = {**build_record(bull_call(chain), catalog), "id": "x", "status": "aberta"}
    ev = evaluate(rec, chain, calendar=calendar)
    plan = ev["exit_plan"]
    assert plan["available"]
    costs = [leg["cross_cost_brl"] for leg in plan["legs"]]
    assert costs[plan["market_leg"]] <= costs[plan["limit_leg"]]
    assert plan["natural_net"] * 100 == pytest.approx(ev["value_natural"])
