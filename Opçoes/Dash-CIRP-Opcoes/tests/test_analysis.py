from __future__ import annotations

import datetime as dt
import math

import pandas as pd
import pytest
from conftest import SIGMA, SPOT, TODAY, make_params, synthetic_chain

from travas.options.analysis import analyze, find_pair, prepare_chain, simulation_grid
from travas.options.liquidity import FLAG_NO_BOOK, FLAG_STALE
from travas.options.models import Direction, Flow, VerticalKind

ALL = [
    (Direction.BULL, Flow.DEBIT, VerticalKind.BULL_CALL_DEBIT),
    (Direction.BEAR, Flow.DEBIT, VerticalKind.BEAR_PUT_DEBIT),
    (Direction.BULL, Flow.CREDIT, VerticalKind.BULL_PUT_CREDIT),
    (Direction.BEAR, Flow.CREDIT, VerticalKind.BEAR_CALL_CREDIT),
]


@pytest.mark.parametrize(("direction", "flow", "kind"), ALL)
def test_analysis_produces_valid_structures(chain, calendar, direction, flow, kind):
    target = 34.0 if direction is Direction.BULL else 28.0
    params = make_params(direction, flow, target_price=target)
    result = analyze(chain, SPOT, TODAY, calendar, params)
    rows = result["results"]
    assert rows, result["discarded"]
    for row in rows:
        assert row["kind"] == kind.value
        long_leg, short_leg = row["legs"]
        assert long_leg["option_type"] == short_leg["option_type"] == kind.option_type.value
        width = row["width"]
        units = row["units"]
        entry = row["entry_per_unit"]
        assert 0 < entry < width
        if flow is Flow.DEBIT:
            assert entry == pytest.approx(long_leg["ask"] - short_leg["bid"])
            assert row["max_loss"] == pytest.approx(entry * units)
            assert row["max_profit"] == pytest.approx((width - entry) * units)
        else:
            assert entry == pytest.approx(short_leg["bid"] - long_leg["ask"])
            assert row["max_profit"] == pytest.approx(entry * units)
            assert row["max_loss"] == pytest.approx((width - entry) * units)
        if direction is Direction.BULL:
            assert long_leg["strike"] < short_leg["strike"]
        else:
            assert long_leg["strike"] > short_leg["strike"]
        assert len(row["breakevens"]) == 1
        assert 0 < row["pop"] < 1
        assert 0 <= row["score"] <= 100
        assert row["limit"]["suggested"] is not None
    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))


def test_iv_recovered_from_synthetic_prices(chain, calendar):
    prep = prepare_chain(chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.DEBIT))
    assert prep.atm["atm_iv"].to_numpy() == pytest.approx([SIGMA, SIGMA], abs=0.02)


def test_scenario_at_expiry_matches_payoff(chain, calendar):
    params = make_params(Direction.BULL, Flow.DEBIT, target_price=40.0)
    rows = analyze(chain, SPOT, TODAY, calendar, params)["results"]
    for row in rows:  # alvo acima de todos os strikes → lucro máximo no vencimento
        assert row["scenario_at_expiry"]
        assert row["scenario_pnl"] == pytest.approx(row["max_profit"])


def test_scenario_before_expiry_uses_model(chain, calendar):
    params = make_params(
        Direction.BULL, Flow.DEBIT, target_price=33.0, horizon_date=dt.date(2026, 10, 23)
    )
    rows = analyze(chain, SPOT, TODAY, calendar, params)["results"]
    row = rows[0]
    assert not row["scenario_at_expiry"]
    assert "valor teórico" in row["scenarios"][0]["basis"]
    assert -row["max_loss"] <= row["scenario_pnl"] <= row["max_profit"]


def test_pop_omitted_without_volatility(calendar):
    chain = synthetic_chain(calendar)
    chain["spread_pct_mid"] = 0.9  # nenhuma série serve para IV ATM
    params = make_params(
        Direction.BULL, Flow.DEBIT, liquidity=make_params(Direction.BULL, Flow.DEBIT).liquidity
    )
    params = make_params(Direction.BULL, Flow.DEBIT, include_illiquid=True)
    rows = analyze(chain, SPOT, TODAY, calendar, params)["results"]
    assert rows
    for row in rows:
        assert row["pop"] is None
        assert row["pop_unavailable_reason"]
        assert row["score_components"]["pop"]["effective_weight"] == 0


def test_stale_quotes_flagged_and_excluded(calendar):
    chain = synthetic_chain(calendar)
    stale = chain["strike"] == 32.0
    chain.loc[stale, "quote_age_seconds"] = 5_000.0
    params = make_params(Direction.BULL, Flow.DEBIT)
    result = analyze(chain, SPOT, TODAY, calendar, params)
    assert all(
        32.0 not in (r["legs"][0]["strike"], r["legs"][1]["strike"]) for r in result["results"]
    )
    assert result["discarded"]["perna com liquidez/cotação reprovada"] > 0

    included = analyze(
        chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.DEBIT, include_illiquid=True)
    )["results"]
    flagged = [r for r in included if FLAG_STALE in r["data_flags"]]
    assert flagged
    assert all(r["score"] <= 40 for r in flagged)
    assert all(not r["liquidity_ok"] for r in flagged)


def test_missing_book_is_not_estimable(calendar):
    chain = synthetic_chain(calendar)
    chain.loc[chain["strike"] == 30.0, ["bid", "mid", "spread_pct_mid"]] = math.nan
    result = analyze(
        chain, SPOT, TODAY, calendar, make_params(Direction.BULL, Flow.DEBIT, include_illiquid=True)
    )
    # Comprada no 30 sem ask? Não: falta o bid → só a vendida no 30 fica sem preço natural.
    assert result["discarded"].get("sem bid/ask para o preço natural (não estimável)", 0) > 0
    for row in result["results"]:
        if 30.0 in (leg["strike"] for leg in row["legs"]):
            assert FLAG_NO_BOOK in row["data_flags"]
            assert row["limit"]["suggested"] is None


def test_budget_filter(chain, calendar):
    params = make_params(Direction.BULL, Flow.DEBIT, max_loss_total=50.0)
    result = analyze(chain, SPOT, TODAY, calendar, params)
    assert all(r["max_loss"] <= 50.0 for r in result["results"])
    assert result["discarded"]["perda máxima acima do orçamento"] > 0


def test_weights_change_ranking(chain, calendar):
    by_rr = make_params(
        Direction.BULL,
        Flow.DEBIT,
        weights={"scenario": 0, "reward_risk": 1, "pop": 0, "liquidity": 0, "execution_cost": 0},
    )
    rows = analyze(chain, SPOT, TODAY, calendar, by_rr)["results"]
    rr = [r["reward_risk"] for r in rows]
    assert rr[0] == pytest.approx(max(rr))
    by_pop = make_params(
        Direction.BULL,
        Flow.DEBIT,
        weights={"scenario": 0, "reward_risk": 0, "pop": 1, "liquidity": 0, "execution_cost": 0},
    )
    rows = analyze(chain, SPOT, TODAY, calendar, by_pop)["results"]
    pops = [r["pop"] for r in rows]
    assert pops[0] == pytest.approx(max(pops))


def test_simulation_converges_to_expiry_payoff(chain, calendar):
    params = make_params(Direction.BULL, Flow.DEBIT, target_price=33.0)
    prep = prepare_chain(chain, SPOT, TODAY, calendar, params)
    exp = dt.date(2026, 11, 13)
    long_sym = chain[
        (chain.strike == 30) & (chain.option_type == "call") & (chain.expiration_date == exp)
    ].symbol.iloc[0]
    short_sym = chain[
        (chain.strike == 32) & (chain.option_type == "call") & (chain.expiration_date == exp)
    ].symbol.iloc[0]
    grid = simulation_grid(prep, *find_pair(prep, long_sym, short_sym))
    assert grid["model_available"]
    last = grid["dates"][-1]
    assert last["date"] == exp.isoformat()
    assert last["business_days_left"] == 0
    assert last["pnl"] == pytest.approx(grid["expiry_pnl"], abs=0.02)
    first = grid["dates"][0]
    # Antes do vencimento o valor teórico é mais "suave": no strike menor perde menos que no venc.
    i = min(range(len(grid["spots"])), key=lambda k: abs(grid["spots"][k] - 30.0))
    assert first["pnl"][i] > grid["expiry_pnl"][i]


def test_dates_are_iso(chain, calendar):
    result = analyze(chain, SPOT, TODAY, calendar, make_params(Direction.BEAR, Flow.CREDIT))
    assert all(isinstance(pd.Timestamp(r["expiration"]), pd.Timestamp) for r in result["results"])
