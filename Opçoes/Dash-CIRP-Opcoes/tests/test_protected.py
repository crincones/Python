"""Ativo protegido: collar e collar + borboleta (ativo + put + calls vendidas)."""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import RATE_ANNUAL, SETTINGS, SPOT, TODAY, synthetic_chain

from travas.options import pricing
from travas.options.liquidity import FLAG_STALE, LiquidityRules
from travas.options.protected import (
    Piece,
    ProtectedKind,
    ProtectedParams,
    StockQuote,
    cdi_period,
    collar_fly_pieces,
    collar_pieces,
    evaluate,
    expiry_profile,
    find_rows,
    intervals_at_or_above,
    prepare,
    prob_value_at_least,
    scan_prepared,
    simulation,
    value_at_expiry,
)

STOCK = StockQuote("TEST3", 30.99, 31.0, SPOT, SPOT, "2026-10-14T11:00:00-03:00", "mt5")


def make_params(**kw) -> ProtectedParams:
    s = SETTINGS
    defaults = dict(
        quantity=100,
        rate_annual=RATE_ANNUAL,
        liquidity=LiquidityRules(
            max_spread_pct_mid=0.5,
            min_mid_price_brl=0.03,
            min_turnover_brl=0,
            min_deals=1,
            max_quote_age_seconds=300,
        ),
        weights=s.protected.weights.model_dump(),
        pricing=s.pricing,
        early_exercise=s.early_exercise,
        dte_min=1,
        dte_max=90,
    )
    defaults.update(kw)
    return ProtectedParams(**defaults)


def scan(calendar, chain=None, stock=STOCK, **kw):
    chain = synthetic_chain(calendar) if chain is None else chain
    prep = prepare(chain, stock, SPOT, TODAY, calendar, make_params(**kw))
    return prep, scan_prepared(prep)


# ---------- payoff ----------


@pytest.mark.parametrize(
    ("spot", "expected"),
    [(150, 183), (183, 183), (186, 186), (190, 190), (195, 190), (250, 190)],
)
def test_collar_value(spot, expected):
    assert value_at_expiry(collar_pieces(183, 190), [spot])[0] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("spot", "expected"),
    [
        (100, 183),  # abaixo da put: put garante o strike
        (183, 183),
        (187, 187),  # entre a put e as calls vendidas: acompanha o ativo
        (190, 190),  # máximo nas calls vendidas
        (192, 188),  # 2·190 − 192
        (195, 185),  # 2·190 − 195
        (300, 185),  # acima da call comprada: plano
    ],
)
def test_collar_fly_value(spot, expected):
    pieces = collar_fly_pieces(183, 190, 195)
    assert value_at_expiry(pieces, [spot])[0] == pytest.approx(expected)


def test_video_example_returns():
    """Exemplo do vídeo (BOVA11): put 183, 2 calls 190 vendidas, call 195, custo 178,81."""
    prof = expiry_profile(collar_fly_pieces(183, 190, 195))
    cost = 178.81
    assert prof.floor == 183 and prof.cap == 190 and prof.cap_at == 190
    assert prof.low_tail == 183 and prof.high_tail == 185
    assert prof.low_tail / cost - 1 == pytest.approx(0.0234, abs=5e-5)  # queda: 2,34%
    assert prof.high_tail / cost - 1 == pytest.approx(0.0346, abs=5e-5)  # alta forte: 3,46%
    # Máximo exato 6,26% (o vídeo arredonda para 6,24%).
    assert prof.cap / cost - 1 == pytest.approx(0.0626, abs=5e-5)


def test_floor_is_wing_when_wing_is_wide():
    # 2·K1 − K2 = 2·190 − 200 = 180 < put 183 → piso é a asa, não a put.
    prof = expiry_profile(collar_fly_pieces(183, 190, 200))
    assert prof.floor == 180


@pytest.mark.parametrize(
    "pieces",
    [
        (Piece("stock", 1), Piece("put", 1, 183), Piece("call", -2, 190)),  # sem call comprada
        (Piece("stock", 1), Piece("call", -1, 190)),  # sem put: sem piso
        (Piece("put", 1, 183), Piece("call", -1, 190)),  # sem o ativo
    ],
)
def test_unbounded_structures_rejected(pieces):
    with pytest.raises(ValueError):
        expiry_profile(pieces)


def test_intervals_and_probability_match_lognormal():
    pieces = collar_pieces(30, 33)
    assert intervals_at_or_above(pieces, 31.5) == [(pytest.approx(31.5), float("inf"))]
    assert intervals_at_or_above(pieces, 29) == [(0.0, float("inf"))]
    assert intervals_at_or_above(pieces, 34) == []
    fly = collar_fly_pieces(30, 33, 35)
    lo, hi = intervals_at_or_above(fly, 32)[0]
    assert (lo, hi) == (pytest.approx(32), pytest.approx(34))
    r = float(pricing.continuous_rate(RATE_ANNUAL))
    p = prob_value_at_least(pieces, 31.5, SPOT, 0.1, r, 0.3)
    assert p == pytest.approx(float(pricing.prob_above(SPOT, 31.5, 0.1, r, 0.3)))


def test_cdi_period():
    assert cdi_period(0.14, 252) == pytest.approx(0.14)
    assert cdi_period(0.14, 21) == pytest.approx(1.14 ** (21 / 252) - 1)


# ---------- varredura ----------


def test_scan_only_risk_zero(calendar):
    _, out = scan(calendar)
    rows = out["results"]
    assert rows, out["discarded"]
    kinds = {r["kind"] for r in rows}
    assert kinds == {"collar", "collar_borboleta"}
    for r in rows:
        assert r["risk_zero"]
        assert r["floor_value"] >= r["cost_natural"] - 1e-9
        assert r["min_profit"] >= -1e-6
        assert r["floor_return"] <= r["unchanged_return"] + 1e-9 <= r["max_return"] + 2e-9
        k = r["strikes"]
        assert k["put"] < k["short_call"]
        if r["kind"] == "collar_borboleta":
            assert k["short_call"] < k["long_call"]
            assert [leg["ratio"] for leg in r["legs"]] == [1, 2, 1]
            assert [leg["side"] for leg in r["legs"]] == ["compra", "venda", "compra"]
        assert r["score"] is not None
    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))


def test_natural_cost_by_leg_sides(calendar):
    prep, out = scan(calendar)
    r = next(r for r in out["results"] if r["kind"] == "collar_borboleta")
    put, short, long_ = r["legs"]
    expected = STOCK.ask + put["ask"] - 2 * short["bid"] + long_["ask"]
    assert r["cost_natural"] == pytest.approx(expected)
    # Piso exato: mínimo entre a put e a asa (2·K1 − K2).
    k = r["strikes"]
    assert r["floor_value"] == pytest.approx(min(k["put"], 2 * k["short_call"] - k["long_call"]))


def test_floor_never_beats_cdi_much_with_fair_prices(calendar):
    """Paridade put-call: com preços justos (cadeia sintética) o piso não supera o CDI."""
    _, out = scan(calendar)
    assert all(r["floor_return"] <= r["cdi_period"] + 1e-9 for r in out["results"])


def test_min_floor_return_filters(calendar):
    _, base = scan(calendar)
    _, strict = scan(calendar, min_floor_return=0.005)
    assert strict["total_ranked"] < base["total_ranked"]
    assert all(r["floor_return"] >= 0.005 - 1e-9 for r in strict["results"])


def test_costs_reduce_returns(calendar):
    prep, out = scan(calendar)
    r0 = out["results"][0]
    prep2, _ = scan(calendar, costs_brl=10.0)
    kind, rows = find_rows(prep2, r0["id"])
    r1 = evaluate(prep2, kind, rows)
    assert r1["max_profit"] == pytest.approx(r0["max_profit"] - 10.0)
    assert r1["floor_return"] < r0["floor_return"]


def test_only_selected_kinds(calendar):
    _, out = scan(calendar, kinds=(ProtectedKind.COLLAR,))
    assert out["results"] and all(r["kind"] == "collar" for r in out["results"])


def test_prob_omitted_without_iv(calendar):
    pricing_no_atm = SETTINGS.pricing.model_copy(update={"atm_max_spread_pct_mid": 1e-9})
    _, out = scan(calendar, pricing=pricing_no_atm)
    assert out["results"]
    for r in out["results"]:
        assert r["prob_beat_cdi"] is None
        assert r["prob_unavailable_reason"]
    _, with_iv = scan(calendar)
    assert all(0 <= r["prob_beat_cdi"] <= 1 for r in with_iv["results"])
    assert all(r["prob_method"] for r in with_iv["results"])


def test_stale_quotes_flagged_and_excluded(calendar):
    chain = synthetic_chain(calendar)
    chain.loc[chain["option_type"] == "put", "quote_age_seconds"] = 10_000
    _, out = scan(calendar, chain=chain)
    assert out["results"] == []
    assert out["discarded"]["série com liquidez/cotação reprovada"] > 0
    _, incl = scan(calendar, chain=chain, include_illiquid=True)
    assert incl["results"]
    for r in incl["results"]:
        assert not r["liquidity_ok"]
        assert FLAG_STALE in r["data_flags"]
        assert r["score"] <= 40 + 1e-9


def test_stock_without_book_is_flagged(calendar):
    stock = StockQuote("TEST3", None, None, None, SPOT, None, "ultimo_pregao")
    _, out = scan(calendar, stock=stock)
    flags = out["stock"]["flags"]
    assert any("sem book" in f for f in flags)
    assert any("fora do pregão" in f for f in flags)
    assert all(f in out["results"][0]["data_flags"] for f in flags)


def test_european_short_filter(calendar):
    # Na cadeia sintética todas as calls são americanas.
    _, out = scan(calendar, european_short=True)
    assert out["results"] == []
    assert out["discarded"]["call vendida americana (filtro de estilo)"] > 0


def test_limit_price_between_mid_and_natural(calendar):
    _, out = scan(calendar)
    for r in out["results"][:30]:
        lim = r["limit"]
        assert lim["mid"] - 0.01 <= lim["suggested"] <= lim["natural"] + 1e-9
        assert lim["suggested"] <= lim["max_cost"] + 1e-9
        assert lim["impacts"]["sugerido"]["floor_return"] >= r["floor_return"] - 1e-9


def test_simulation_curves(calendar):
    prep, out = scan(calendar)
    r = next(r for r in out["results"] if r["kind"] == "collar_borboleta")
    kind, rows = find_rows(prep, r["id"])
    sim = simulation(prep, kind, rows)
    assert sim["model_available"]
    xs = pd.Series(sim["spots"])
    ys = pd.Series(sim["expiry_pnl"])
    assert ys.min() == pytest.approx(r["min_profit"], abs=0.02)
    assert ys.max() <= r["max_profit"] + 0.02
    # Último pregão = vencimento: modelo converge para o payoff exato.
    last = sim["dates"][-1]
    assert last["business_days_left"] == 0
    assert last["pnl"] == pytest.approx(sim["expiry_pnl"], abs=0.02)
    assert len(xs) == len(ys)


def test_find_rows_unknown(calendar):
    prep, _ = scan(calendar)
    with pytest.raises(KeyError):
        find_rows(prep, "collar:XXX|YYY")
    with pytest.raises(KeyError):
        find_rows(prep, "outra:XXX")


def test_results_include_best_european_short(calendar):
    """Lista = melhores no geral ∪ melhores com call vendida europeia (filtro na interface)."""
    chain = synthetic_chain(calendar)
    chain.loc[(chain["option_type"] == "call") & (chain["strike"] >= 34), "exercise_style"] = (
        "european"
    )
    _, full = scan(calendar, chain=chain)
    _, out = scan(calendar, chain=chain, max_results=5)
    european = [r for r in full["results"] if r["legs"][1]["exercise_style"] == "european"]
    assert european and out["total_european_short"] == len(european)
    ids = [r["id"] for r in out["results"]]
    expected = {r["id"] for r in full["results"][:5]} | {r["id"] for r in european[:5]}
    assert set(ids) == expected
    ranks = [r["rank"] for r in out["results"]]
    assert ranks == sorted(ranks)  # ordem do ranking geral preservada


def test_options_package_flow(calendar):
    """Pacote de opções (sem o ativo): + débito, − crédito; a estrutura inteira é sempre débito."""
    _, out = scan(calendar)
    flows = set()
    for r in out["results"]:
        o = r["options"]
        assert o["net_natural"] == pytest.approx(r["cost_natural"] - STOCK.ask)
        assert o["net_mid"] == pytest.approx(r["cost_mid"] - (STOCK.bid + STOCK.ask) / 2)
        expected = (
            "debito"
            if o["net_natural"] > 0.005
            else "credito"
            if o["net_natural"] < -0.005
            else "zero"
        )
        assert o["flow_natural"] == expected
        assert o["flow_differs"] == (o["flow_natural"] != o["flow_mid"])
        assert r["cost_natural"] > 0  # com o ativo, sempre débito
        flows.add(o["flow_natural"])
    assert {"debito", "credito"} <= flows


def test_options_flow_threshold():
    from travas.options.protected import _flow

    assert _flow(0.01) == "debito"
    assert _flow(-0.01) == "credito"
    assert _flow(0.004) == "zero"
    assert _flow(None) is None
