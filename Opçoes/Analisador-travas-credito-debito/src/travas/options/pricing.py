"""Black-Scholes europeu, vetorizado com numpy. Funções puras, sem dividendos.

Convenções:
- T em anos de dias úteis: T = dias úteis / 252 (`year_fraction`).
- r contínua: r = ln(1 + taxa anual composta em 252 dias úteis) (`continuous_rate`), de modo que
  e^(r·T) = (1 + CDI)^(du/252).
- `is_call` booleano (True = call, False = put). Todos os argumentos aceitam escalares ou arrays
  com broadcasting.
- Theta por ano (divida por 252 para theta por dia útil). Vega e rho por 1,00 de variação
  (divida por 100 para "por ponto percentual").
- Calls americanas sem dividendos valem o mesmo que europeias; puts americanas e ativos com
  proventos antes do vencimento ficam aproximados (limitação documentada na UI).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import ndtr

BUSINESS_DAYS_PER_YEAR = 252

FloatArray = NDArray[np.float64]


def continuous_rate(annual_rate: ArrayLike) -> FloatArray:
    return np.log1p(np.asarray(annual_rate, dtype=np.float64))


def year_fraction(business_days: ArrayLike) -> FloatArray:
    return np.asarray(business_days, dtype=np.float64) / BUSINESS_DAYS_PER_YEAR


def _norm_pdf(x: FloatArray) -> FloatArray:
    return np.exp(-0.5 * x * x) / np.sqrt(2.0 * np.pi)


def _broadcast(*args: ArrayLike) -> list[FloatArray]:
    return [np.asarray(a, dtype=np.float64) for a in np.broadcast_arrays(*args)]


def d1_d2(
    spot: ArrayLike, strike: ArrayLike, t: ArrayLike, rate: ArrayLike, sigma: ArrayLike
) -> tuple[FloatArray, FloatArray]:
    """d1 e d2. Com T ≤ 0 ou σ ≤ 0 o resultado é ±inf/NaN; use as funções de preço, que tratam."""
    s, k, t_, r, v = _broadcast(spot, strike, t, rate, sigma)
    with np.errstate(divide="ignore", invalid="ignore"):
        vol_sqrt_t = v * np.sqrt(t_)
        d1 = (np.log(s / k) + (r + 0.5 * v * v) * t_) / vol_sqrt_t
    return d1, d1 - vol_sqrt_t


def discount_factor(rate: ArrayLike, t: ArrayLike) -> FloatArray:
    r, t_ = _broadcast(rate, t)
    return np.exp(-r * t_)


def price(
    spot: ArrayLike,
    strike: ArrayLike,
    t: ArrayLike,
    rate: ArrayLike,
    sigma: ArrayLike,
    is_call: ArrayLike,
) -> FloatArray:
    """Prêmio europeu. Com T ≤ 0 ou σ ≤ 0 devolve o valor intrínseco descontado do forward."""
    s, k, t_, r, v, call = _broadcast(spot, strike, t, rate, sigma, is_call)
    call = call.astype(bool)
    df = np.exp(-r * np.clip(t_, 0.0, None))
    degenerate = (t_ <= 0) | (v <= 0)

    d1, d2 = d1_d2(s, k, np.where(degenerate, 1.0, t_), r, np.where(degenerate, 1.0, v))
    call_value = s * ndtr(d1) - k * df * ndtr(d2)
    put_value = k * df * ndtr(-d2) - s * ndtr(-d1)
    value = np.where(call, call_value, put_value)

    intrinsic_forward = np.where(call, s - k * df, k * df - s).clip(min=0.0)
    return np.where(degenerate, intrinsic_forward, value)


def price_scalar(
    spot: float, strike: float, t: float, rate: float, sigma: float, is_call: bool
) -> float:
    """Mesmo resultado de `price` para um único contrato, sem overhead do numpy.

    Usada como função-objetivo do brentq (milhares de avaliações por snapshot). Exige T > 0 e
    σ > 0; o chamador trata os casos degenerados.
    """
    vol_sqrt_t = sigma * math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * t) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    k_pv = strike * math.exp(-rate * t)
    if is_call:
        return spot * _norm_cdf_scalar(d1) - k_pv * _norm_cdf_scalar(d2)
    return k_pv * _norm_cdf_scalar(-d2) - spot * _norm_cdf_scalar(-d1)


def _norm_cdf_scalar(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def no_arbitrage_bounds(
    spot: ArrayLike, strike: ArrayLike, t: ArrayLike, rate: ArrayLike, is_call: ArrayLike
) -> tuple[FloatArray, FloatArray]:
    """Limites (inferior, superior) do prêmio europeu sem dividendos."""
    s, k, t_, r, call = _broadcast(spot, strike, t, rate, is_call)
    call = call.astype(bool)
    k_pv = k * np.exp(-r * t_)
    lower = np.where(call, s - k_pv, k_pv - s).clip(min=0.0)
    upper = np.where(call, s, k_pv)
    return lower, upper


def greeks(
    spot: ArrayLike,
    strike: ArrayLike,
    t: ArrayLike,
    rate: ArrayLike,
    sigma: ArrayLike,
    is_call: ArrayLike,
) -> dict[str, FloatArray]:
    """delta, gamma, vega, theta (por ano) e rho. NaN quando T ≤ 0 ou σ ≤ 0."""
    s, k, t_, r, v, call = _broadcast(spot, strike, t, rate, sigma, is_call)
    call = call.astype(bool)
    valid = (t_ > 0) & (v > 0)
    t_safe = np.where(valid, t_, np.nan)
    v_safe = np.where(valid, v, np.nan)
    d1, d2 = d1_d2(s, k, t_safe, r, v_safe)
    df = np.exp(-r * t_safe)
    pdf_d1 = _norm_pdf(d1)
    sqrt_t = np.sqrt(t_safe)

    gamma = pdf_d1 / (s * v_safe * sqrt_t)
    vega = s * pdf_d1 * sqrt_t
    decay = -s * pdf_d1 * v_safe / (2.0 * sqrt_t)
    return {
        "delta": np.where(call, ndtr(d1), ndtr(d1) - 1.0),
        "gamma": gamma,
        "vega": vega,
        "theta": np.where(call, decay - r * k * df * ndtr(d2), decay + r * k * df * ndtr(-d2)),
        "rho": np.where(call, k * t_safe * df * ndtr(d2), -k * t_safe * df * ndtr(-d2)),
    }


def prob_above(
    spot: ArrayLike, level: ArrayLike, t: ArrayLike, rate: ArrayLike, sigma: ArrayLike
) -> FloatArray:
    """P(S_T > level) sob a medida neutra ao risco (lognormal, drift r). NaN se T ≤ 0 ou σ ≤ 0."""
    s, lvl, t_, r, v = _broadcast(spot, level, t, rate, sigma)
    valid = (t_ > 0) & (v > 0) & (lvl > 0)
    _, d2 = d1_d2(s, np.where(valid, lvl, np.nan), t_, r, v)
    return np.where(valid, ndtr(d2), np.nan)


def prob_itm(
    spot: ArrayLike,
    strike: ArrayLike,
    t: ArrayLike,
    rate: ArrayLike,
    sigma: ArrayLike,
    is_call: ArrayLike,
) -> FloatArray:
    """Probabilidade neutra ao risco de terminar ITM: N(d2) para call, N(−d2) para put."""
    above = prob_above(spot, strike, t, rate, sigma)
    call = np.asarray(is_call, dtype=bool)
    return np.where(call, above, 1.0 - above)
