"""Motor de payoff das quatro travas verticais. Dados fictícios só aqui, nos testes."""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pytest

from travas.options.models import (
    Direction,
    Flow,
    Leg,
    OptionType,
    Side,
    Structure,
    VerticalKind,
)
from travas.options.payoff import (
    MissingPriceError,
    expiry_profile,
    leg_pnl_at_expiry,
    net_premium,
    pnl_at_expiry,
    profit_intervals,
)
from travas.options.validation import validate_vertical

EXP = dt.date(2026, 11, 20)
QTY = 100


def leg(kind: OptionType, side: Side, strike: float, price: float | None, **kw) -> Leg:
    return Leg(kind, side, strike, kw.pop("expiration", EXP), kw.pop("quantity", QTY), 1.0, price)


def vertical(kind: OptionType, long_k: float, long_p: float, short_k: float, short_p: float):
    return Structure(
        "TEST3",
        (leg(kind, Side.LONG, long_k, long_p), leg(kind, Side.SHORT, short_k, short_p)),
    )


C, P = OptionType.CALL, OptionType.PUT
# Strikes 30 e 32 (largura 2), quantidade 100.
BULL_CALL_DEBIT = vertical(C, 30, 1.50, 32, 0.70)  # débito 0,80
BEAR_PUT_DEBIT = vertical(P, 32, 1.60, 30, 0.75)  # débito 0,85
BULL_PUT_CREDIT = vertical(P, 30, 0.75, 32, 1.60)  # crédito 0,85
BEAR_CALL_CREDIT = vertical(C, 32, 0.70, 30, 1.50)  # crédito 0,80

# estrutura, tipo, fluxo por unidade, lucro máx/un, perda máx/un, breakeven
CASES = [
    (BULL_CALL_DEBIT, VerticalKind.BULL_CALL_DEBIT, -0.80, 1.20, 0.80, 30.80),
    (BEAR_PUT_DEBIT, VerticalKind.BEAR_PUT_DEBIT, -0.85, 1.15, 0.85, 31.15),
    (BULL_PUT_CREDIT, VerticalKind.BULL_PUT_CREDIT, 0.85, 0.85, 1.15, 31.15),
    (BEAR_CALL_CREDIT, VerticalKind.BEAR_CALL_CREDIT, 0.80, 0.80, 1.20, 30.80),
]


@pytest.mark.parametrize(("structure", "kind", "flow", "gain", "loss", "be"), CASES)
def test_profile_matches_closed_form(structure, kind, flow, gain, loss, be):
    profile = expiry_profile(structure)
    assert profile.net_premium == pytest.approx(flow * QTY)
    assert profile.max_profit == pytest.approx(gain * QTY)
    assert profile.max_loss == pytest.approx(loss * QTY)
    assert profile.breakevens == pytest.approx((be,))
    assert profile.reward_risk == pytest.approx(gain / loss)
    assert profile.risk_reward == pytest.approx(loss / gain)
    assert pnl_at_expiry(structure, [be])[0] == pytest.approx(0.0, abs=1e-9)
    validation = validate_vertical(structure, kind.direction, kind.flow)
    assert validation.ok, validation.errors
    assert validation.kind is kind


@pytest.mark.parametrize(("structure", "kind", "flow", "gain", "loss", "be"), CASES)
def test_extremes_match_dense_grid(structure, kind, flow, gain, loss, be):
    grid = np.linspace(0.01, 100, 200_001)
    pnl = pnl_at_expiry(structure, grid)
    assert pnl.max() == pytest.approx(gain * QTY, abs=1e-6)
    assert pnl.min() == pytest.approx(-loss * QTY, abs=1e-6)


@pytest.mark.parametrize(
    ("structure", "below", "between", "above"),
    [
        # preços: 25 (abaixo), 31 (entre), 40 (acima)
        (BULL_CALL_DEBIT, -80.0, 20.0, 120.0),
        (BEAR_PUT_DEBIT, 115.0, 15.0, -85.0),
        (BULL_PUT_CREDIT, -115.0, -15.0, 85.0),
        (BEAR_CALL_CREDIT, 80.0, -20.0, -120.0),
    ],
)
def test_pnl_below_between_above(structure, below, between, above):
    assert pnl_at_expiry(structure, [25, 31, 40]) == pytest.approx([below, between, above])


def test_debit_reduces_and_credit_increases_result():
    no_premium = vertical(C, 30, 0.0, 32, 0.0)
    debit = BULL_CALL_DEBIT
    assert np.all(pnl_at_expiry(debit, [25, 31, 40]) < pnl_at_expiry(no_premium, [25, 31, 40]))
    no_premium_put = vertical(P, 30, 0.0, 32, 0.0)
    assert np.all(
        pnl_at_expiry(BULL_PUT_CREDIT, [25, 31, 40]) > pnl_at_expiry(no_premium_put, [25, 31, 40])
    )


def test_costs_shift_result_and_breakeven():
    base = expiry_profile(BULL_CALL_DEBIT)
    with_costs = expiry_profile(BULL_CALL_DEBIT, costs=10.0)
    assert with_costs.max_profit == pytest.approx(base.max_profit - 10)
    assert with_costs.max_loss == pytest.approx(base.max_loss + 10)
    assert with_costs.breakevens[0] == pytest.approx(30.90)


def test_swapping_sides_mirrors_profile():
    swapped = vertical(C, 32, 0.70, 30, 1.50)  # = BEAR_CALL_CREDIT
    grid = np.array([25.0, 30.5, 31.0, 40.0])
    assert pnl_at_expiry(swapped, grid) == pytest.approx(-pnl_at_expiry(BULL_CALL_DEBIT, grid))
    assert validate_vertical(swapped).kind is VerticalKind.BEAR_CALL_CREDIT


def test_inverting_strikes_changes_kind():
    # Mesmas pernas de put, mas comprada no strike menor: vira alta com crédito.
    inverted = vertical(P, 30, 0.75, 32, 1.60)
    assert validate_vertical(inverted).kind is VerticalKind.BULL_PUT_CREDIT
    assert validate_vertical(BEAR_PUT_DEBIT).kind is VerticalKind.BEAR_PUT_DEBIT


def test_label_mismatch_is_invalid():
    result = validate_vertical(BULL_CALL_DEBIT, Direction.BEAR, Flow.DEBIT)
    assert not result.ok
    assert any("não 'Trava de baixa com débito" in e for e in result.errors)


def test_inconsistent_prices_are_invalid():
    # Call de strike menor mais barata que a de strike maior: "alta com débito" geraria crédito.
    broken = vertical(C, 30, 0.50, 32, 0.70)
    result = validate_vertical(broken)
    assert not result.ok
    assert any("deveria gerar débito" in e for e in result.errors)
    # Débito maior que a largura: sem lucro possível.
    too_expensive = vertical(C, 30, 2.80, 32, 0.70)
    assert any("largura" in e for e in validate_vertical(too_expensive).errors)


@pytest.mark.parametrize(
    ("legs", "message"),
    [
        ((leg(C, Side.LONG, 30, 1), leg(P, Side.SHORT, 32, 1)), "classes diferentes"),
        ((leg(C, Side.LONG, 30, 1), leg(C, Side.LONG, 32, 1)), "mesmo lado"),
        ((leg(C, Side.LONG, 30, 1), leg(C, Side.SHORT, 30, 1)), "strikes iguais"),
        ((leg(C, Side.LONG, 30, 1), leg(C, Side.SHORT, 32, 1, quantity=200)), "desbalanceada"),
        (
            (leg(C, Side.LONG, 30, 1), leg(C, Side.SHORT, 32, 1, expiration=dt.date(2026, 12, 18))),
            "calendário/diagonal",
        ),
    ],
)
def test_invalid_geometry(legs, message):
    result = validate_vertical(Structure("TEST3", legs))
    assert not result.ok
    assert result.kind is None
    assert any(message in e for e in result.errors)


def test_missing_price():
    structure = vertical(C, 30, 1.5, 32, 0.7).with_prices([1.5, None])
    with pytest.raises(MissingPriceError):
        net_premium(structure)
    result = validate_vertical(structure)
    assert result.kind is VerticalKind.BULL_CALL_DEBIT
    assert result.warnings


def test_leg_pnl_sums_to_structure():
    grid = np.array([20.0, 31.0, 45.0])
    total = sum(leg_pnl_at_expiry(lg, grid) for lg in BULL_CALL_DEBIT.legs)
    assert total == pytest.approx(pnl_at_expiry(BULL_CALL_DEBIT, grid))


def test_profit_intervals():
    assert profit_intervals(BULL_CALL_DEBIT) == [(pytest.approx(30.8), math.inf)]
    assert profit_intervals(BEAR_PUT_DEBIT) == [(0.0, pytest.approx(31.15))]


def test_unlimited_profile_detected():
    naked_call = Structure("TEST3", (leg(C, Side.LONG, 30, 1.0),))
    profile = expiry_profile(naked_call)
    assert math.isinf(profile.max_profit)
    assert profile.max_loss == pytest.approx(100)
    short_call = Structure("TEST3", (leg(C, Side.SHORT, 30, 1.0),))
    assert math.isinf(expiry_profile(short_call).max_loss)
