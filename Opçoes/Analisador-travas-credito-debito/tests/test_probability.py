from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pytest

from travas.options.models import Leg, OptionType, Side, Structure
from travas.options.pricing import prob_above
from travas.options.probability import pop_at_expiry, prob_finish_beyond, prob_touch

EXP = dt.date(2026, 11, 20)
BULL = Structure(
    "TEST3",
    (
        Leg(OptionType.CALL, Side.LONG, 30, EXP, 100, 1.0, 1.50),
        Leg(OptionType.CALL, Side.SHORT, 32, EXP, 100, 1.0, 0.70),
    ),
)
BEAR = Structure(
    "TEST3",
    (
        Leg(OptionType.PUT, Side.LONG, 32, EXP, 100, 1.0, 1.60),
        Leg(OptionType.PUT, Side.SHORT, 30, EXP, 100, 1.0, 0.75),
    ),
)
SPOT, T, R, SIGMA = 31.0, 25 / 252, math.log1p(0.14), 0.35


def test_pop_bull_equals_prob_above_breakeven():
    pop = pop_at_expiry(BULL, SPOT, T, R, SIGMA, "teste")
    assert pop.value == pytest.approx(float(prob_above(SPOT, 30.80, T, R, SIGMA)))
    assert "não antes" in pop.method


def test_pop_bear_equals_prob_below_breakeven():
    pop = pop_at_expiry(BEAR, SPOT, T, R, SIGMA, "teste")
    assert pop.value == pytest.approx(1 - float(prob_above(SPOT, 31.15, T, R, SIGMA)))


def test_pop_against_monte_carlo():
    rng = np.random.default_rng(7)
    z = rng.standard_normal(400_000)
    st = SPOT * np.exp((R - 0.5 * SIGMA**2) * T + SIGMA * math.sqrt(T) * z)
    from travas.options.payoff import pnl_at_expiry

    mc = float((pnl_at_expiry(BULL, st) > 0).mean())
    assert pop_at_expiry(BULL, SPOT, T, R, SIGMA, "teste").value == pytest.approx(mc, abs=0.003)


@pytest.mark.parametrize(
    ("spot", "t", "sigma"), [(31.0, T, None), (31.0, T, 0.0), (31.0, 0.0, 0.3), (0.0, T, 0.3)]
)
def test_pop_omitted_without_assumptions(spot, t, sigma):
    pop = pop_at_expiry(BULL, spot, t, R, sigma, "teste")
    assert pop.value is None
    assert pop.reason


def test_finish_beyond_complementary():
    up = prob_finish_beyond(SPOT, 33, True, T, R, SIGMA).value
    down = prob_finish_beyond(SPOT, 33, False, T, R, SIGMA).value
    assert up + down == pytest.approx(1.0)


def test_touch_exceeds_finish_and_matches_zero_drift_formula():
    touch = prob_touch(SPOT, 34, T, 0.0, SIGMA).value
    finish = prob_finish_beyond(SPOT, 34, True, T, 0.0, SIGMA).value
    assert touch > finish
    # Sem drift no log (ν = 0) a reflexão dá exatamente 2·P(S_T ≥ H); com drift 0 no preço, ν < 0.
    nu_zero_drift = 0.5 * SIGMA**2
    touch_nu0 = prob_touch(SPOT, 34, T, nu_zero_drift, SIGMA).value
    finish_nu0 = prob_finish_beyond(SPOT, 34, True, T, nu_zero_drift, SIGMA).value
    assert touch_nu0 == pytest.approx(2 * finish_nu0)
    below = prob_touch(SPOT, 28, T, nu_zero_drift, SIGMA).value
    assert below == pytest.approx(
        2 * prob_finish_beyond(SPOT, 28, False, T, nu_zero_drift, SIGMA).value
    )
