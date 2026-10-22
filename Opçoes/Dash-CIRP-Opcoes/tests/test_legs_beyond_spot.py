"""Filtro de strikes: as 2 pernas abaixo do spot (trava de alta) ou acima (trava de baixa)."""

from __future__ import annotations

import pytest
from conftest import SPOT, TODAY, make_params, synthetic_chain

from travas.options.analysis import analyze
from travas.options.models import Direction, Flow


def strikes(rows):
    return [leg["strike"] for r in rows for leg in r["legs"]]


@pytest.mark.parametrize("flow", [Flow.DEBIT, Flow.CREDIT])
@pytest.mark.parametrize("direction", [Direction.BULL, Direction.BEAR])
def test_both_legs_on_the_side_against_the_move(calendar, direction, flow):
    chain = synthetic_chain(calendar)
    base = analyze(chain, SPOT, TODAY, calendar, make_params(direction, flow))
    out = analyze(chain, SPOT, TODAY, calendar, make_params(direction, flow, legs_beyond_spot=True))
    assert out["results"] and len(out["results"]) < len(base["results"])
    if direction is Direction.BULL:
        assert all(k < SPOT for k in strikes(out["results"]))
        assert any(k >= SPOT for k in strikes(base["results"]))
        assert "abaixo" in out["assumptions"]["strike_side_filter"]
    else:
        assert all(k > SPOT for k in strikes(out["results"]))
        assert "acima" in out["assumptions"]["strike_side_filter"]
    assert base["assumptions"]["strike_side_filter"] is None


def test_empty_result_explains_the_filter(calendar):
    params = make_params(Direction.BULL, Flow.DEBIT, legs_beyond_spot=True, strike_min=SPOT)
    out = analyze(synthetic_chain(calendar), SPOT, TODAY, calendar, params)
    assert out["results"] == []
    assert "as 2 pernas abaixo do preço do ativo" in out["empty_reason"]
