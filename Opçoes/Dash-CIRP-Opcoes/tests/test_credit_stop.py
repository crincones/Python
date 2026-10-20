"""Stop 1:1 em travas de crédito: fronteira do stop, Monte Carlo do manejo e ranking."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest
from conftest import SETTINGS, SIGMA, SPOT, TODAY, make_params

from travas.options import pricing
from travas.options.analysis import CREDIT_STOP_COMPONENTS, analyze
from travas.options.credit_stop import (
    NOT_APPLICABLE_REASON,
    close_cost,
    credit_stop_metrics,
    stop_boundary,
)
from travas.options.models import Direction, Flow, Leg, OptionType, Side, Structure

RATE = float(pricing.continuous_rate(0.14))
EXP = dt.date(2026, 11, 13)
DTE = 22


def _spread(kind: str, short_k: float, long_k: float) -> Structure:
    option = OptionType.PUT if kind == "put" else OptionType.CALL
    return Structure(
        "TEST3",
        (
            Leg(option, Side.LONG, long_k, EXP, 100, 1.0, None, "L"),
            Leg(option, Side.SHORT, short_k, EXP, 100, 1.0, None, "S"),
        ),
    )


def _credit(structure: Structure) -> float:
    return float(close_cost(structure, np.array(SPOT), np.array(DTE / 252), RATE, [SIGMA] * 2))


@pytest.mark.parametrize(
    ("kind", "short_k", "long_k", "down"), [("put", 29.0, 27.0, True), ("call", 33.0, 35.0, False)]
)
def test_boundary_hits_trigger_and_is_exact_at_expiry(kind, short_k, long_k, down):
    s = _spread(kind, short_k, long_k)
    credit = _credit(s)
    trigger = 2 * credit
    boundary = stop_boundary(s, trigger, DTE, RATE, [SIGMA] * 2, down)
    expected_expiry = short_k - trigger if down else short_k + trigger
    assert boundary[-1] == pytest.approx(expected_expiry, abs=1e-6)
    taus = (DTE - np.arange(DTE + 1)) / 252
    cost = close_cost(s, boundary, taus, RATE, [SIGMA] * 2)
    assert cost == pytest.approx(np.full(DTE + 1, trigger), abs=1e-6)
    # Hoje o stop fica entre o spot e o strike vendido (perda = crédito antes do strike).
    assert (boundary[0] < SPOT) if down else (boundary[0] > SPOT)


def _metrics(short_k: float, long_k: float, **kw):
    s = _spread("put", short_k, long_k)
    credit = _credit(s)
    return credit_stop_metrics(
        s, credit, credit, short_k - long_k, DTE, SPOT, RATE, [SIGMA] * 2, SIGMA, **kw
    )


def test_fair_credit_has_expected_value_near_zero():
    # Sob o modelo, crédito = valor teórico → resultado esperado ≈ 0 com ou sem stop.
    m, reason = _metrics(29.0, 27.0)
    assert reason is None
    credit = m["stop_loss_per_unit"]  # sem custo de saída: perda no stop = crédito
    assert m["expected_pnl_per_unit"] == pytest.approx(0.0, abs=0.04 * credit)
    assert m["expected_pnl_no_stop_per_unit"] == pytest.approx(0.0, abs=0.04 * credit)
    assert 0 < m["prob_stop"] < 1
    assert m["prob_full_credit"] <= m["prob_profit"] <= m["prob_no_stop"] + 1e-12


@pytest.mark.parametrize("short_k", [31.0, 29.0, 27.0])
def test_fair_credit_stop_is_a_coin_flip_at_any_distance(short_k):
    # Crédito justo: dobrar o crédito antes de zerar tem ~50% de chance, perto ou longe. Travas
    # longe pagam pouco e o stop fica perto do spot no começo (muito valor de tempo).
    m, _ = _metrics(short_k, short_k - 2)
    assert m["prob_stop"] == pytest.approx(0.5, abs=0.04)


def test_rich_sold_option_lowers_stop_probability():
    # IV da vendida acima da σ dos caminhos (skew): crédito "caro" → stop menos provável, EV > 0.
    s = _spread("put", 29.0, 27.0)
    sigmas = [SIGMA + 0.05, SIGMA + 0.10]  # comprada, vendida
    taus = np.array(DTE / 252)
    credit = float(close_cost(s, np.array(SPOT), taus, RATE, sigmas))
    m, _ = credit_stop_metrics(s, credit, credit, 2.0, DTE, SPOT, RATE, sigmas, SIGMA)
    fair, _ = _metrics(29.0, 27.0)
    assert m["prob_stop"] < fair["prob_stop"] - 0.03
    assert m["expected_pnl_per_unit"] > 0


def test_exit_cost_enters_the_stop_loss():
    s = _spread("put", 29.0, 27.0)
    natural = _credit(s) - 0.05  # crédito natural 0,05 abaixo do mid
    args = (2.0, DTE, SPOT, RATE, [SIGMA] * 2, SIGMA)
    with_cost, _ = credit_stop_metrics(s, natural, natural + 0.05, *args)
    no_cost, _ = credit_stop_metrics(s, natural, natural, *args)
    assert with_cost["exit_cost_per_unit"] == pytest.approx(0.05)
    assert with_cost["stop_loss_per_unit"] == pytest.approx(natural + 0.05)
    assert with_cost["expected_pnl_per_unit"] < no_cost["expected_pnl_per_unit"]
    assert credit_stop_metrics(s, natural, natural + 0.05, *args)[0] == with_cost  # mesmos sorteios


def test_not_applicable_when_credit_half_width():
    s = _spread("put", 29.0, 27.0)
    assert credit_stop_metrics(s, 1.0, 1.0, 2.0, DTE, SPOT, RATE, [SIGMA] * 2, SIGMA) == (
        None,
        NOT_APPLICABLE_REASON,
    )


def test_analysis_ranks_credit_spreads_with_stop(calendar, chain):
    params = make_params(
        Direction.BULL,
        Flow.CREDIT,
        credit_stop=True,
        credit_stop_paths=1000,
        credit_stop_weights=SETTINGS.credit_stop.weights.model_dump(),
    )
    result = analyze(chain, SPOT, TODAY, calendar, params)
    rows = result["results"]
    assert rows and result["credit_stop"]["active"]
    assert NOT_APPLICABLE_REASON in result["discarded"]  # travas com crédito ≥ metade da largura
    for row in rows:
        stop = row["credit_stop"]
        short_k = row["legs"][1]["strike"]  # trava de alta com puts: stop abaixo da vendida
        assert stop["stop_price_expiry"] == pytest.approx(short_k - 2 * row["entry_natural"])
        assert set(row["score_components"]) == set(CREDIT_STOP_COMPONENTS)
        assert row["entry_natural"] * 2 < row["width"]
    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)


def test_credit_stop_ignored_for_debit(calendar, chain):
    params = make_params(Direction.BULL, Flow.DEBIT, credit_stop=True)
    result = analyze(chain, SPOT, TODAY, calendar, params)
    assert result["credit_stop"]["active"] is False
    assert all("credit_stop" not in r for r in result["results"])
