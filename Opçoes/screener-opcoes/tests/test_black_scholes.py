from __future__ import annotations

import numpy as np
import pytest

from screener.pricing import black_scholes as bs

RNG = np.random.default_rng(20260917)


def _random_market(n: int = 500) -> dict[str, np.ndarray]:
    return {
        "spot": RNG.uniform(5, 200, n),
        "strike": RNG.uniform(5, 200, n),
        "t": RNG.uniform(1 / 252, 1.0, n),
        "rate": RNG.uniform(0.0, 0.2, n),
        "sigma": RNG.uniform(0.05, 1.5, n),
    }


def test_hull_reference_values() -> None:
    # Hull, Options, Futures and Other Derivatives, exemplo 15.6: S=42, K=40, r=10%, σ=20%, T=0,5.
    call = bs.price(42, 40, 0.5, 0.10, 0.20, True)
    put = bs.price(42, 40, 0.5, 0.10, 0.20, False)
    d1, d2 = bs.d1_d2(42, 40, 0.5, 0.10, 0.20)
    assert float(d1) == pytest.approx(0.7693, abs=1e-4)
    assert float(d2) == pytest.approx(0.6278, abs=1e-4)
    assert float(call) == pytest.approx(4.76, abs=5e-3)
    assert float(put) == pytest.approx(0.81, abs=5e-3)


def test_scalar_price_matches_vectorized() -> None:
    m = _random_market(200)
    for is_call in (True, False):
        vectorized = bs.price(**m, is_call=is_call)
        scalar = [
            bs.price_scalar(s, k, t, r, v, is_call)
            for s, k, t, r, v in zip(
                m["spot"], m["strike"], m["t"], m["rate"], m["sigma"], strict=True
            )
        ]
        np.testing.assert_allclose(scalar, vectorized, rtol=1e-12, atol=1e-12)


def test_put_call_parity_vectorized() -> None:
    m = _random_market()
    call = bs.price(**m, is_call=True)
    put = bs.price(**m, is_call=False)
    parity = m["spot"] - m["strike"] * np.exp(-m["rate"] * m["t"])
    np.testing.assert_allclose(call - put, parity, atol=1e-9)


def test_price_respects_no_arbitrage_bounds() -> None:
    m = _random_market()
    for is_call in (True, False):
        value = bs.price(**m, is_call=is_call)
        lower, upper = bs.no_arbitrage_bounds(m["spot"], m["strike"], m["t"], m["rate"], is_call)
        assert (value >= lower - 1e-9).all()
        assert (value <= upper + 1e-9).all()


def test_degenerate_inputs_return_discounted_intrinsic() -> None:
    at_expiry = bs.price([50, 50], [45, 55], 0.0, 0.1, 0.3, [True, False])
    np.testing.assert_allclose(at_expiry, [5.0, 5.0])
    zero_vol = bs.price(50, 45, 1.0, 0.1, 0.0, True)
    assert float(zero_vol) == pytest.approx(50 - 45 * np.exp(-0.1))


def test_continuous_rate_matches_brazilian_compounding() -> None:
    cdi, business_days = 0.149, 37
    t = bs.year_fraction(business_days)
    assert float(np.exp(bs.continuous_rate(cdi) * t)) == pytest.approx(
        (1 + cdi) ** (business_days / 252)
    )


@pytest.mark.parametrize("is_call", [True, False])
def test_greeks_match_finite_differences(is_call: bool) -> None:
    s, k, t, r, v = 48.3, 50.0, 20 / 252, 0.139, 0.32
    g = bs.greeks(s, k, t, r, v, is_call)

    def p(**kw: float) -> float:
        args = {"spot": s, "strike": k, "t": t, "rate": r, "sigma": v} | kw
        return float(bs.price(**args, is_call=is_call))

    h = 1e-4
    assert float(g["delta"]) == pytest.approx((p(spot=s + h) - p(spot=s - h)) / (2 * h), abs=1e-6)
    gamma_fd = (p(spot=s + h) - 2 * p() + p(spot=s - h)) / h**2
    assert float(g["gamma"]) == pytest.approx(gamma_fd, rel=1e-3)
    assert float(g["vega"]) == pytest.approx((p(sigma=v + h) - p(sigma=v - h)) / (2 * h), rel=1e-6)
    assert float(g["rho"]) == pytest.approx((p(rate=r + h) - p(rate=r - h)) / (2 * h), rel=1e-6)
    # theta = ∂V/∂(tempo corrido) = −∂V/∂T
    assert float(g["theta"]) == pytest.approx(-(p(t=t + h) - p(t=t - h)) / (2 * h), rel=1e-5)


def test_greeks_are_nan_when_degenerate() -> None:
    g = bs.greeks(50, 50, 0.0, 0.1, 0.3, True)
    assert all(np.isnan(value) for value in g.values())


def test_prob_itm_is_minus_strike_derivative_of_price() -> None:
    # e^(−rT)·N(d2) = −∂C/∂K (preço de digital): valida a probabilidade neutra ao risco.
    s, k, t, r, v = 42.0, 40.0, 0.5, 0.1, 0.2
    h = 1e-4
    dc_dk = (bs.price(s, k + h, t, r, v, True) - bs.price(s, k - h, t, r, v, True)) / (2 * h)
    prob = bs.prob_itm(s, k, t, r, v, True)
    assert float(np.exp(-r * t) * prob) == pytest.approx(float(-dc_dk), rel=1e-6)


def test_prob_itm_call_and_put_sum_to_one() -> None:
    m = _random_market()
    total = bs.prob_itm(**m, is_call=True) + bs.prob_itm(**m, is_call=False)
    np.testing.assert_allclose(total, 1.0)


def test_prob_above_is_nan_without_time_or_vol() -> None:
    assert np.isnan(bs.prob_above(50, 55, 0.0, 0.1, 0.3))
    assert np.isnan(bs.prob_above(50, 55, 0.5, 0.1, 0.0))
