"""Pricing sobre o snapshot real de 17/09/2026."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from screener.pricing import black_scholes as bs
from screener.pricing.implied_vol import IVStatus, options_implied_vol
from screener.settings import load_settings

# Taxa implícita na paridade put-call de BOVA11 em 17/09/2026 (ver CLAUDE.md).
FIXTURE_RATE = 0.129


@pytest.fixture(scope="module")
def priced(fixture_options: pd.DataFrame) -> pd.DataFrame:
    settings = load_settings()
    return fixture_options.join(
        options_implied_vol(fixture_options, FIXTURE_RATE, settings.pricing)
    )


def test_iv_converges_for_almost_all_quoted_series(priced: pd.DataFrame) -> None:
    quoted = priced[priced["mid"].notna()]
    assert (quoted["iv_status"] == IVStatus.OK.value).mean() > 0.95
    assert (priced.loc[priced["mid"].isna(), "iv_status"] == IVStatus.NO_PRICE.value).all()
    assert priced.loc[priced["iv_status"] != IVStatus.OK.value, "iv"].isna().all()


def test_liquid_series_have_plausible_iv(priced: pd.DataFrame) -> None:
    rules = load_settings().series_liquidity
    liquid = priced[
        (priced["spread_pct_mid"] <= rules.max_spread_pct_mid)
        & (priced["turnover_brl"] >= rules.min_turnover_brl)
        & (priced["deals"] >= rules.min_deals)
    ]
    ok = liquid[liquid["iv_status"] == IVStatus.OK.value]
    assert len(ok) / len(liquid) > 0.95
    assert ok["iv"].between(0.10, 1.0).all()


def test_atm_iv_by_underlying_is_plausible(priced: pd.DataFrame) -> None:
    ok = priced[(priced["iv_status"] == IVStatus.OK.value)].assign(
        moneyness=lambda d: (d["strike"] / d["underlying_price"] - 1).abs()
    )
    monthly = ok[ok["expiration_date"] == pd.Timestamp("2026-10-16")]
    atm = monthly.sort_values("moneyness").groupby("underlying").head(2)
    atm_iv = atm.groupby("underlying")["iv"].mean()
    assert len(atm_iv) == 20
    assert atm_iv.between(0.15, 0.80).all()
    assert atm_iv["BOVA11"] < atm_iv["PETR4"]  # ETF de índice menos volátil que ação isolada


def test_repricing_with_iv_recovers_mid(priced: pd.DataFrame) -> None:
    ok = priced[priced["iv_status"] == IVStatus.OK.value]
    repriced = bs.price(
        ok["underlying_price"],
        ok["strike"],
        ok["t_years"],
        ok["rate"],
        ok["iv"],
        (ok["option_type"] == "call").to_numpy(),
    )
    np.testing.assert_allclose(repriced, ok["mid"], atol=1e-4)


def test_bova11_parity_implies_configured_fixture_rate(fixture_options: pd.DataFrame) -> None:
    eu = fixture_options[
        (fixture_options["underlying"] == "BOVA11")
        & (fixture_options["exercise_style"] == "european")
        & (fixture_options["spread_pct_mid"] <= 0.05)
    ]
    keys = ["expiration_date", "strike"]
    calls = eu[eu["option_type"] == "call"].set_index(keys)
    puts = eu[eu["option_type"] == "put"].set_index(keys)
    pairs = calls[["mid", "underlying_price", "dte_business_days"]].join(
        puts[["mid"]], rsuffix="_put", how="inner"
    )
    pairs = pairs.reset_index()
    pairs = pairs[(pairs["strike"] / pairs["underlying_price"] - 1).abs() <= 0.05]
    discount = (pairs["underlying_price"] - (pairs["mid"] - pairs["mid_put"])) / pairs["strike"]
    implied = discount ** (-252 / pairs["dte_business_days"]) - 1
    assert len(pairs) >= 5
    assert float(implied.median()) == pytest.approx(FIXTURE_RATE, abs=0.005)
