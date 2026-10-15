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


def test_one_third_is_more_permissive(calendar):
    chain = synthetic_chain(calendar)
    quarter = analyze(
        chain,
        SPOT,
        TODAY,
        calendar,
        make_params(Direction.BULL, Flow.DEBIT, target_price=33.0, nobre_filter=True),
    )["results"]
    third = analyze(
        chain,
        SPOT,
        TODAY,
        calendar,
        make_params(
            Direction.BULL,
            Flow.DEBIT,
            target_price=33.0,
            nobre_filter=True,
            nobre_max_cost_fraction=1 / 3,
        ),
    )["results"]
    assert len(third) > len(quarter)
    for r in third:
        assert r["entry_natural"] <= r["width"] / 3 + 1e-9
        assert r["reward_risk"] >= 2 - 1e-9
        assert r["limit"]["suggested"] <= r["width"] / 3 + 1e-9
    assert any(r["entry_natural"] > r["width"] / 4 for r in third)  # passou só com 1/3


def test_closer_strikes_first(calendar):
    chain = synthetic_chain(calendar)
    params = make_params(
        Direction.BULL,
        Flow.DEBIT,
        target_price=36.0,
        nobre_filter=True,
        nobre_max_cost_fraction=1 / 3,
    )
    rows = analyze(chain, SPOT, TODAY, calendar, params)["results"]
    assert len({r["width"] for r in rows}) > 1
    ok = [r for r in rows if r["nobre"]["target_ok"] is not False]
    widths = [r["width"] for r in ok]
    assert widths == sorted(widths)  # menor largura primeiro
    for w in set(widths):  # empate de largura → maior score primeiro
        scores = [r["score"] for r in ok if r["width"] == w]
        assert scores == sorted(scores, reverse=True)
    by_score = analyze(
        chain,
        SPOT,
        TODAY,
        calendar,
        make_params(
            Direction.BULL,
            Flow.DEBIT,
            target_price=36.0,
            nobre_filter=True,
            nobre_max_cost_fraction=1 / 3,
            nobre_prefer_close=False,
        ),
    )["results"]
    ok2 = [r["score"] for r in by_score if r["nobre"]["target_ok"] is not False]
    assert ok2 == sorted(ok2, reverse=True)


def test_warns_when_no_structure_meets_both_rules(calendar):
    chain = synthetic_chain(calendar)
    # Alvo logo acima do spot: vendida antes do alvo ⇒ trava cara demais para 1/4.
    params = make_params(Direction.BULL, Flow.DEBIT, target_price=31.5, nobre_filter=True)
    result = analyze(chain, SPOT, TODAY, calendar, params)
    assert result["results"]
    assert result["nobre"]["both_rules"] == 0
    assert "Nenhuma trava cumpre as duas regras" in result["nobre"]["warning"]
    far = analyze(
        chain,
        SPOT,
        TODAY,
        calendar,
        make_params(Direction.BULL, Flow.DEBIT, target_price=36.0, nobre_filter=True),
    )
    assert far["nobre"]["both_rules"] > 0 and far["nobre"]["warning"] is None
