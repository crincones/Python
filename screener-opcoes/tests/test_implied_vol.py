from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from screener.pricing import black_scholes as bs
from screener.pricing.implied_vol import IVStatus, implied_volatility, options_implied_vol
from screener.settings import load_settings

PRICING = load_settings().pricing


def test_recovers_known_volatility_grid() -> None:
    spot = 48.3
    strikes = np.array([38.0, 44.0, 48.0, 52.0, 58.0])
    t = bs.year_fraction(np.array([5, 20, 43]))[:, None, None]
    sigmas = np.array([0.12, 0.35, 0.9])[None, :, None]
    rate = bs.continuous_rate(0.149)
    for is_call in (True, False):
        premium = bs.price(spot, strikes[None, None, :], t, rate, sigmas, is_call)
        iv, status = implied_volatility(premium, spot, strikes, t, rate, is_call, PRICING)
        # Prêmios muito próximos do limite inferior (OTM curto com vol baixa) não identificam σ.
        identifiable = premium - bs.no_arbitrage_bounds(spot, strikes, t, rate, is_call)[0] > 1e-4
        ok = status == IVStatus.OK.value
        assert ok[identifiable].all()
        expected = np.broadcast_to(sigmas, premium.shape)
        np.testing.assert_allclose(iv[identifiable], expected[identifiable], atol=1e-5)


def test_invalid_premiums_get_status_and_nan() -> None:
    spot, strike, t, rate = 50.0, 45.0, 0.1, 0.13
    lower, upper = bs.no_arbitrage_bounds(spot, strike, t, rate, True)
    premiums = np.array([np.nan, 0.0, float(lower) - 0.01, float(upper) + 1.0, 5.6])
    ts = np.array([t, t, t, t, 0.0])
    iv, status = implied_volatility(premiums, spot, strike, ts, rate, True, PRICING)
    assert status.tolist() == [
        IVStatus.NO_PRICE.value,
        IVStatus.NO_PRICE.value,
        IVStatus.BELOW_INTRINSIC.value,
        IVStatus.ABOVE_UPPER.value,
        IVStatus.EXPIRED.value,
    ]
    assert np.isnan(iv).all()


def test_volatility_outside_configured_range_is_rejected() -> None:
    narrow = PRICING.model_copy(update={"iv_lower_bound": 0.2, "iv_upper_bound": 0.5})
    premium = bs.price(50, 50, 0.25, 0.1, 0.9, True)
    iv, status = implied_volatility(premium, 50, 50, 0.25, 0.1, True, narrow)
    assert status.item() == IVStatus.OUT_OF_RANGE.value
    assert np.isnan(iv).all()


def test_european_itm_put_below_intrinsic_still_has_iv() -> None:
    # Caso real da fixture: ABEVV170, put europeia ITM cotada abaixo de K − S (juros de ~14%).
    t = bs.year_fraction(20)
    rate = bs.continuous_rate(0.149)
    mid = (1.44 + 1.47) / 2
    assert mid < 17.05 - 15.55
    iv, status = implied_volatility(mid, 15.55, 17.05, t, rate, False, PRICING)
    assert status.item() == IVStatus.OK.value
    assert 0 < iv.item() < 1


def test_options_implied_vol_keeps_index() -> None:
    options = pd.DataFrame(
        {
            "mid": [0.525, np.nan],
            "underlying_price": [48.3, 48.3],
            "strike": [48.17, 48.17],
            "dte_business_days": [1, 1],  # PETRI49 vencia em 18/09
            "option_type": ["call", "put"],
        },
        index=[10, 11],
    )
    result = options_implied_vol(options, 0.149, PRICING)
    assert list(result.index) == [10, 11]
    assert result.loc[11, "iv_status"] == IVStatus.NO_PRICE.value
    assert result.loc[10, "iv_status"] == IVStatus.OK.value
    assert 0 < result.loc[10, "iv"] < 1
    assert result.loc[10, "t_years"] == pytest.approx(1 / 252)
