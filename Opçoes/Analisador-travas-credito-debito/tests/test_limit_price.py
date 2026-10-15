from __future__ import annotations

import datetime as dt

import pytest

from travas.options.limit_price import impact, suggest_limit, with_entry
from travas.options.models import Flow, Leg, OptionType, Side, Structure

EXP = dt.date(2026, 11, 20)


def _vertical(kind, long_k, long_p, short_k, short_p):
    return Structure(
        "TEST3",
        (
            Leg(kind, Side.LONG, long_k, EXP, 100, 1.0, long_p),
            Leg(kind, Side.SHORT, short_k, EXP, 100, 1.0, short_p),
        ),
    )


BULL_CALL = _vertical(OptionType.CALL, 30, 1.50, 32, 0.70)  # natural 0,80
BULL_PUT = _vertical(OptionType.PUT, 30, 0.75, 32, 1.60)  # crédito natural 0,85


def test_debit_suggestion_between_mid_and_natural_rounded_down():
    limit = suggest_limit(
        BULL_CALL, Flow.DEBIT, 2.0, natural=0.80, mid=0.70, theoretical=0.72, aggressiveness=0.25
    )
    assert limit.suggested == pytest.approx(0.72)  # 0,725 → arredonda para baixo
    assert (limit.range_low, limit.range_high) == (0.70, 0.80)
    imp = limit.impacts["sugerido"]
    assert imp.max_loss == pytest.approx(72.0)
    assert imp.max_profit == pytest.approx(128.0)
    assert imp.breakevens == pytest.approx((30.72,))


def test_credit_suggestion_rounded_up():
    limit = suggest_limit(
        BULL_PUT, Flow.CREDIT, 2.0, natural=0.85, mid=0.95, theoretical=None, aggressiveness=0.25
    )
    assert limit.suggested == pytest.approx(0.93)  # 0,925 → arredonda para cima
    imp = limit.impacts["sugerido"]
    assert imp.max_profit == pytest.approx(93.0)
    assert imp.max_loss == pytest.approx(107.0)
    assert imp.breakevens == pytest.approx((31.07,))


def test_min_reward_risk_caps_debit():
    limit = suggest_limit(BULL_CALL, Flow.DEBIT, 2.0, 0.80, 0.70, None, 0.25, min_reward_risk=2.0)
    assert limit.suggested == pytest.approx(0.66)  # 2/(1+2) = 0,666… → 0,66
    assert any("lucro/perda mínima" in n for n in limit.notes)
    assert any("melhor que o mid" in n for n in limit.notes)


def test_budget_floors_credit():
    # Perda máxima ≤ R$ 100 → crédito ≥ 2 − 1 = 1,00
    limit = suggest_limit(BULL_PUT, Flow.CREDIT, 2.0, 0.85, 0.95, None, 0.25, max_loss_total=100.0)
    assert limit.suggested == pytest.approx(1.00)


def test_not_estimable_without_book():
    limit = suggest_limit(BULL_CALL, Flow.DEBIT, 2.0, None, 0.70, None, 0.25)
    assert limit.suggested is None
    assert "não estimável" in limit.reason_unavailable


def test_entry_changes_profile_consistently():
    cheaper = impact(BULL_CALL, 0.60, Flow.DEBIT)
    pricier = impact(BULL_CALL, 0.90, Flow.DEBIT)
    assert cheaper.max_profit > pricier.max_profit
    assert cheaper.max_loss < pricier.max_loss
    assert cheaper.breakevens[0] < pricier.breakevens[0]
    s = with_entry(BULL_PUT, 1.0, Flow.CREDIT)
    long_leg, short_leg = s.legs
    assert short_leg.price - long_leg.price == pytest.approx(1.0)
