"""Filtro de estilo de exercício por perna (europeia x americana)."""

from __future__ import annotations

from conftest import SPOT, TODAY, make_params, synthetic_chain

from travas.options.analysis import EUROPEAN_SHORT_REASON, analyze
from travas.options.models import Direction, Flow


def mixed_chain(calendar):
    """Calls de strike par europeias, ímpar americanas (a XP mistura os dois estilos)."""
    chain = synthetic_chain(calendar)
    calls = chain["option_type"] == "call"
    chain.loc[calls, "exercise_style"] = [
        "european" if int(k) % 2 == 0 else "american" for k in chain.loc[calls, "strike"]
    ]
    return chain


def styles(rows):
    return {(r["legs"][0]["exercise_style"], r["legs"][1]["exercise_style"]) for r in rows}


def test_european_short_only(calendar):
    chain = mixed_chain(calendar)
    base = analyze(chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.DEBIT))
    assert ("european", "american") in styles(base["results"])  # sem filtro aparecem as duas
    result = analyze(
        chain,
        SPOT,
        TODAY,
        calendar,
        make_params(Direction.BULL, Flow.DEBIT, european_short=True),
    )
    assert result["results"]
    assert all(r["legs"][1]["exercise_style"] == "european" for r in result["results"])
    assert result["discarded"][EUROPEAN_SHORT_REASON] > 0
    assert result["assumptions"]["exercise_style_filter"] == ["perna vendida europeia"]


def test_puts_already_european_unaffected(calendar):
    # Alta com crédito usa puts; na XP (e nesta cadeia) todas são europeias.
    chain = mixed_chain(calendar)
    off = analyze(chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.CREDIT))
    on = analyze(
        chain,
        SPOT,
        TODAY,
        calendar,
        make_params(Direction.BULL, Flow.CREDIT, european_short=True),
    )
    assert len(on["results"]) == len(off["results"])
