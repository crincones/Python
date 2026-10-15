"""Filtro Rafael Nobre (travas de débito): vendida antes do alvo e custo ≤ 1/4 da largura."""

from __future__ import annotations

import pytest
from conftest import SPOT, TODAY, make_params, synthetic_chain

from travas.options.analysis import (
    NOBRE_COST_REASON,
    NOBRE_TARGET_REASON,
    analyze,
    nobre_check,
)
from travas.options.models import Direction, Flow, VerticalKind


@pytest.mark.parametrize(
    ("kind", "short_k", "target", "expected"),
    [
        (VerticalKind.BULL_CALL_DEBIT, 33, 34, True),  # vendida 33 antes do alvo 34
        (VerticalKind.BULL_CALL_DEBIT, 34, 34, True),  # no alvo conta como antes
        (VerticalKind.BULL_CALL_DEBIT, 35, 34, False),
        (VerticalKind.BEAR_PUT_DEBIT, 29, 28, True),  # baixa: vendida 29 acima do alvo 28
        (VerticalKind.BEAR_PUT_DEBIT, 27, 28, False),
        (VerticalKind.BULL_CALL_DEBIT, 33, None, None),  # sem alvo: não se aplica
    ],
)
def test_target_rule(kind, short_k, target, expected):
    assert nobre_check(kind, short_k, 2.0, 0.40, target)["target_ok"] is expected


def test_cost_rule_quarter_of_width():
    assert nobre_check(VerticalKind.BULL_CALL_DEBIT, 32, 2.0, 0.50, None)["cost_ok"]  # = 1/4
    assert not nobre_check(VerticalKind.BULL_CALL_DEBIT, 32, 2.0, 0.51, None)["cost_ok"]
    assert nobre_check(VerticalKind.BULL_CALL_DEBIT, 32, 2.0, 0.40, None)["cost_ratio"] == 0.2


def test_not_applied_to_credit():
    assert nobre_check(VerticalKind.BULL_PUT_CREDIT, 32, 2.0, 0.40, 34) is None
    assert nobre_check(VerticalKind.BEAR_CALL_CREDIT, 30, 2.0, 0.40, 28) is None


@pytest.mark.parametrize(("direction", "target"), [(Direction.BULL, 33.0), (Direction.BEAR, 29.0)])
def test_filter_in_analysis(calendar, direction, target):
    chain = synthetic_chain(calendar)
    base = analyze(
        chain, SPOT, TODAY, calendar, make_params(direction, Flow.DEBIT, target_price=target)
    )
    params = make_params(direction, Flow.DEBIT, target_price=target, nobre_filter=True)
    result = analyze(chain, SPOT, TODAY, calendar, params)
    rows = result["results"]
    assert rows and len(rows) < len(base["results"])
    assert result["discarded"][NOBRE_COST_REASON] > 0
    for r in rows:
        assert r["entry_natural"] <= r["width"] / 4 + 1e-9
        assert r["reward_risk"] >= 3 - 1e-9
        # preço-limite sugerido também ≤ 1/4 da largura
        assert r["limit"]["suggested"] <= r["width"] / 4 + 1e-9
    # Preferencial: quem cumpre o alvo vem antes de quem não cumpre.
    flags = [r["nobre"]["target_ok"] for r in rows]
    assert flags == sorted(flags, reverse=True)
    assert result["nobre"]["active"]


def test_target_required_discards(calendar):
    chain = synthetic_chain(calendar)
    params = make_params(
        Direction.BULL, Flow.DEBIT, target_price=33.0, nobre_filter=True, nobre_target_required=True
    )
    result = analyze(chain, SPOT, TODAY, calendar, params)
    assert result["discarded"][NOBRE_TARGET_REASON] > 0
    assert all(r["legs"][1]["strike"] <= 33.0 for r in result["results"])


def test_filter_ignored_for_credit(calendar):
    chain = synthetic_chain(calendar)
    on = analyze(
        chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.CREDIT, nobre_filter=True)
    )
    off = analyze(chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.CREDIT))
    assert len(on["results"]) == len(off["results"])
    assert on["nobre"]["active"] is False
