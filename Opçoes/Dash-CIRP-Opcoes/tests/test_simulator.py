"""Garantia estimada, perna de ativo no motor, simulador geral e coerência das cotações.
Dados fictícios só aqui, nos testes."""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest
from conftest import RATE_ANNUAL, SETTINGS, SPOT, TODAY, synthetic_chain

from travas.data.service import chain_spot
from travas.options import pricing
from travas.options.implied_vol import options_implied_vol
from travas.options.liquidity import LiquidityRules, evaluate_liquidity
from travas.options.margin import exit_spread_cost, margin_estimate
from travas.options.models import Leg, OptionType, Side, Structure
from travas.options.payoff import expiry_profile, pnl_at_expiry
from travas.options.simulation import leg_terms, simulate
from travas.options.simulator import SimulationError, evaluate_simulation, resolve_legs
from travas.options.valuation import structure_value

EXP = dt.date(2026, 11, 13)
C, P, S = OptionType.CALL, OptionType.PUT, OptionType.STOCK
RATE = float(pricing.continuous_rate(RATE_ANNUAL))


def leg(kind, side, strike, price, qty=100, exp=EXP, style="european"):
    return Leg(kind, side, strike, exp, qty, 1.0, price, f"{kind}{strike}", style)


def structure(*legs):
    return Structure("TEST3", tuple(legs))


# ---------- garantia ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("legs", "estimated", "conservative", "capital"),
    [
        # trava de alta com crédito (puts 30/32, crédito 0,85): perda máx. = 2 − 0,85
        ((leg(P, Side.LONG, 30, 0.75), leg(P, Side.SHORT, 32, 1.60)), 115.0, 200.0, 115.0),
        # trava de baixa com crédito (calls 30/32, crédito 0,80)
        ((leg(C, Side.LONG, 32, 0.70), leg(C, Side.SHORT, 30, 1.50)), 120.0, 200.0, 120.0),
        # travas de débito: vendida coberta pela comprada → sem garantia; capital = débito
        ((leg(C, Side.LONG, 30, 1.50), leg(C, Side.SHORT, 32, 0.70)), 0.0, 0.0, 80.0),
        ((leg(P, Side.LONG, 32, 1.60), leg(P, Side.SHORT, 30, 0.75)), 0.0, 0.0, 85.0),
    ],
)
def test_vertical_margin(legs, estimated, conservative, capital):
    m = margin_estimate(structure(*legs))
    assert m["available"]
    assert m["estimated"] == pytest.approx(estimated)
    assert m["conservative"] == pytest.approx(conservative)
    assert m["capital_estimated"] == pytest.approx(capital)
    # Numa trava vertical a garantia estimada é a perda máxima (sem custos) ou zero no débito.
    profile = expiry_profile(structure(*legs))
    if profile.net_premium > 0:
        assert m["estimated"] == pytest.approx(profile.max_loss)


def test_margin_unbounded_long_only_and_calendar():
    naked = margin_estimate(structure(leg(C, Side.SHORT, 32, 0.70)))
    assert not naked["available"] and "ilimitado" in naked["reason"]
    naked_put = margin_estimate(structure(leg(P, Side.SHORT, 30, 0.75)))
    assert naked_put["available"]
    assert naked_put["conservative"] == pytest.approx(3000.0)  # strike × unidades
    assert naked_put["estimated"] == pytest.approx(3000.0 - 75.0)
    long_only = margin_estimate(structure(leg(C, Side.LONG, 32, 0.70)))
    assert long_only["estimated"] == 0.0 and long_only["capital_estimated"] == pytest.approx(70.0)
    cal = margin_estimate(
        structure(
            leg(C, Side.SHORT, 32, 0.70),
            leg(C, Side.LONG, 32, 1.10, exp=dt.date(2026, 12, 18)),
        )
    )
    assert not cal["available"]


def test_margin_style_mismatch_note():
    s = structure(
        leg(C, Side.LONG, 32, 0.70, style="european"),
        leg(C, Side.SHORT, 30, 1.50, style="american"),
    )
    assert any("americana" in n for n in margin_estimate(s)["notes"])


def test_covered_call_needs_no_margin():
    s = structure(leg(S, Side.LONG, 0.0, 30.0), leg(C, Side.SHORT, 32, 1.0))
    m = margin_estimate(s)
    assert m["estimated"] == 0.0
    assert m["capital_estimated"] == pytest.approx(2900.0)


def test_exit_spread_cost():
    assert exit_spread_cost([100, 100], [1.0, 0.5], [1.1, 0.6]) == pytest.approx(10.0)
    assert exit_spread_cost([100], [None], [1.0]) is None


# ---------- perna de ativo no motor -------------------------------------------------------------
def test_stock_leg_payoff_covered_call():
    s = structure(leg(S, Side.LONG, 0.0, 30.0), leg(C, Side.SHORT, 32, 1.0))
    assert s.strikes == [32]  # a perna de ativo não tem strike
    assert s.expirations == {EXP}
    p = expiry_profile(s)
    assert p.max_profit == pytest.approx(300.0)  # (32 − 30 + 1) × 100
    assert p.max_loss == pytest.approx(2900.0)  # ativo a zero: (0 − 30 + 1) × 100
    assert p.breakevens == pytest.approx((29.0,))
    assert pnl_at_expiry(s, [31.0])[0] == pytest.approx(200.0)
    short_stock = expiry_profile(structure(leg(S, Side.SHORT, 0.0, 30.0), leg(C, Side.LONG, 32, 1)))
    assert short_stock.max_profit == pytest.approx(2900.0)
    assert short_stock.max_loss == pytest.approx(300.0)  # call comprada limita a alta


def test_stock_leg_model_value_and_exit_identity(calendar):
    s = structure(leg(S, Side.LONG, 0.0, 30.0), leg(C, Side.SHORT, 32, 1.0))
    sigmas = [None, 0.35]
    sim = simulate(s, TODAY, calendar, RATE, RATE_ANNUAL, sigmas, costs=5.0)
    assert sim["model_available"]
    assert sim["entry_cash"] == pytest.approx(-2900.0)
    assert sim["costs"] == 5.0
    day = sim["dates"][3]
    terms = leg_terms(s, calendar, dt.date.fromisoformat(day["date"]))
    xs = np.array(sim["spots"])
    value = structure_value(s, xs, terms, RATE, sigmas)
    exit_value = np.array(day["pnl"]) - sim["entry_cash"] + sim["costs"]
    np.testing.assert_allclose(exit_value, value, atol=0.01)
    # ativo comprado + call vendida: valor do ativo menos a call
    call = pricing.price(xs, 32, terms[1], RATE, 0.35, True)
    np.testing.assert_allclose(value, 100 * xs - 100 * call, atol=1e-6)


# ---------- simulador ---------------------------------------------------------------------------
def quotes_frame(calendar, **kw):
    chain = synthetic_chain(calendar, **kw)
    rules = LiquidityRules(**SETTINGS.liquidity.model_dump())
    chain = chain.join(evaluate_liquidity(chain, rules))
    chain = chain.join(options_implied_vol(chain, RATE_ANNUAL, SETTINGS.pricing))
    return chain.set_index("symbol", drop=False)


def catalog_frame(calendar):
    c = synthetic_chain(calendar)
    return c[
        ["symbol", "underlying", "option_type", "exercise_style", "strike", "expiration_date"]
    ].assign(contract_size=1.0)


STOCK = {
    "symbol": "TEST3",
    "bid": 30.99,
    "ask": 31.0,
    "last": SPOT,
    "price": SPOT,
    "quote_time": None,
    "source": "mt5",
}


def run(calendar, raw_legs, quotes=None, **kw):
    legs = resolve_legs(raw_legs, "TEST3", catalog_frame(calendar))
    return evaluate_simulation(
        legs,
        quotes if quotes is not None else quotes_frame(calendar),
        STOCK,
        SPOT,
        TODAY,
        calendar,
        RATE,
        RATE_ANNUAL,
        SETTINGS.early_exercise,
        max_quote_age_seconds=300,
        **kw,
    )


def test_simulator_natural_prices_and_vertical_numbers(calendar):
    q = quotes_frame(calendar)
    r = run(
        calendar,
        [
            {"symbol": "TESTP1130", "side": "compra", "quantity": 100},
            {"symbol": "TESTP1132", "side": "venda", "quantity": 100},
        ],
        quotes=q,
    )
    long_ask, short_bid = q.loc["TESTP1130", "ask"], q.loc["TESTP1132", "bid"]
    credit = (short_bid - long_ask) * 100
    assert r["legs"][0]["price_source"] == "natural (ask)"
    assert r["legs"][1]["price_source"] == "natural (bid)"
    assert r["entry_cash_total"] == pytest.approx(credit)
    assert r["entry_flow"] == "credito"
    assert r["kind_label"] == "Trava de alta com crédito (puts)"
    assert r["max_loss"] == pytest.approx(200 - credit)
    assert r["margin"]["estimated"] == pytest.approx(200 - credit)
    assert r["pop"] is not None and 0 < r["pop"] < 1
    assert r["simulation"]["model_available"]
    assert r["simulation"]["exit_spread_cost"] > 0
    # zerar agora pelo natural: recompra a vendida no ask e vende a comprada no bid
    close = 100 * q.loc["TESTP1130", "bid"] - 100 * q.loc["TESTP1132", "ask"]
    assert r["close_natural_now"] == pytest.approx(close)
    assert r["pnl_close_natural_now"] == pytest.approx(close + credit)
    assert not r["warnings"]


def test_simulator_given_price_stock_leg_and_ratio(calendar):
    r = run(
        calendar,
        [
            {"kind": "ativo", "side": "compra", "quantity": 200, "price": 30.0},
            {"symbol": "TESTC1132", "side": "venda", "quantity": 200, "price": 1.0},
            {"symbol": "TESTP1128", "side": "compra", "quantity": 200},
        ],
    )
    assert r["legs"][0]["price_source"] == "informado"
    assert r["kind_label"].startswith("Collar")
    assert any("manualmente" in w for w in r["warnings"])
    assert r["max_profit"] == pytest.approx((32 - 30 + 1) * 200 - r["legs"][2]["price_used"] * 200)
    ratio = run(
        calendar,
        [
            {"symbol": "TESTC1131", "side": "compra", "quantity": 100},
            {"symbol": "TESTC1133", "side": "venda", "quantity": 200},
        ],
    )
    assert not ratio["margin"]["available"]  # call vendida a mais: risco ilimitado
    assert ratio["max_loss"] == math.inf


def test_simulator_validation(calendar):
    cat = catalog_frame(calendar)
    with pytest.raises(SimulationError, match="não encontrado"):
        resolve_legs([{"symbol": "XXXX", "side": "compra", "quantity": 1}], "TEST3", cat)
    with pytest.raises(SimulationError, match="opção de TEST3"):
        resolve_legs([{"symbol": "TESTC1131", "side": "compra", "quantity": 1}], "OUTR3", cat)
    with pytest.raises(SimulationError, match="pelo menos uma opção"):
        resolve_legs([{"kind": "ativo", "side": "compra", "quantity": 1}], "TEST3", cat)
    q = quotes_frame(calendar)
    q.loc["TESTC1131", ["bid", "ask", "last", "mid"]] = np.nan
    with pytest.raises(SimulationError, match="sem preço"):
        run(calendar, [{"symbol": "TESTC1131", "side": "compra", "quantity": 1}], quotes=q)


def test_simulator_flags_legs_from_different_captures(calendar):
    q = quotes_frame(calendar)
    q["captured_at"] = pd.Timestamp("2026-10-14 14:06", tz="America/Sao_Paulo")
    q.loc["TESTP1130", "captured_at"] = pd.Timestamp("2026-10-14 11:10", tz="America/Sao_Paulo")
    r = run(
        calendar,
        [
            {"symbol": "TESTP1130", "side": "compra", "quantity": 100},
            {"symbol": "TESTP1132", "side": "venda", "quantity": 100},
        ],
        quotes=q,
    )
    assert any("momentos diferentes" in w for w in r["warnings"])


def test_simulator_calendar_has_no_pop(calendar):
    r = run(
        calendar,
        [
            {"symbol": "TESTC1131", "side": "venda", "quantity": 100},
            {"symbol": "TESTC1231", "side": "compra", "quantity": 100},
        ],
    )
    assert r["pop"] is None and "vencimentos diferentes" in r["pop_unavailable_reason"]
    assert r["kind_label"] == "Calendário"
    assert r["simulation"]["multi_expiry"]


# ---------- coerência das cotações --------------------------------------------------------------
def test_chain_spot_uses_latest_batch_or_store(calendar):
    chain = synthetic_chain(calendar)
    later = chain["read_time"].iloc[0] + pd.Timedelta(minutes=5)
    chain.loc[3, ["read_time", "underlying_price"]] = [later, 30.5]
    assert chain_spot(chain, "mt5", 99.0) == pytest.approx(30.5)
    assert chain_spot(chain, "ultimo_pregao", 99.0) == 99.0  # mesma referência do QuoteStore
    assert chain_spot(chain.iloc[0:0], "mt5", 99.0) == 99.0
