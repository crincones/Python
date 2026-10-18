"""Volatilidade implícita (Black-Scholes europeu) por brentq, série a série."""

from __future__ import annotations

from enum import StrEnum

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from scipy.optimize import brentq

from screener.pricing.black_scholes import (
    FloatArray,
    continuous_rate,
    no_arbitrage_bounds,
    price_scalar,
    year_fraction,
)
from screener.settings import PricingSettings


class IVStatus(StrEnum):
    OK = "ok"
    NO_PRICE = "sem_preco"
    EXPIRED = "vencida"
    BELOW_INTRINSIC = "abaixo_do_limite_inferior"
    ABOVE_UPPER = "acima_do_limite_superior"
    OUT_OF_RANGE = "fora_da_faixa_de_iv"
    NOT_CONVERGED = "nao_convergiu"


def implied_volatility(
    premium: ArrayLike,
    spot: ArrayLike,
    strike: ArrayLike,
    t: ArrayLike,
    rate: ArrayLike,
    is_call: ArrayLike,
    settings: PricingSettings,
) -> tuple[FloatArray, np.ndarray]:
    """IV de cada prêmio. Devolve (iv, status); iv = NaN quando status != ok.

    O prêmio precisa estar estritamente entre os limites de não-arbitragem; a raiz é buscada em
    [iv_lower_bound, iv_upper_bound].
    """
    p, s, k, t_, r, call = (
        np.asarray(a, dtype=np.float64)
        for a in np.broadcast_arrays(premium, spot, strike, t, rate, is_call)
    )
    call = call.astype(bool)
    iv = np.full(p.shape, np.nan)
    status = np.full(p.shape, IVStatus.OK.value, dtype=object)

    lower, upper = no_arbitrage_bounds(s, k, t_, r, call)
    no_price = ~np.isfinite(p) | (p <= 0) | ~np.isfinite(s) | (s <= 0)
    expired = ~no_price & (t_ <= 0)
    below = ~no_price & ~expired & (p <= lower)
    above = ~no_price & ~expired & ~below & (p >= upper)
    status[no_price] = IVStatus.NO_PRICE.value
    status[expired] = IVStatus.EXPIRED.value
    status[below] = IVStatus.BELOW_INTRINSIC.value
    status[above] = IVStatus.ABOVE_UPPER.value

    lo, hi = settings.iv_lower_bound, settings.iv_upper_bound
    candidates = np.flatnonzero(status == IVStatus.OK.value)
    for i in candidates.tolist():
        idx = np.unravel_index(i, p.shape)
        args = (float(s[idx]), float(k[idx]), float(t_[idx]), float(r[idx]))
        target, is_call_i = float(p[idx]), bool(call[idx])

        def objective(
            sigma: float, args: tuple = args, target: float = target, c: bool = is_call_i
        ) -> float:
            return price_scalar(*args, sigma, c) - target

        f_lo, f_hi = objective(lo), objective(hi)
        if f_lo > 0 or f_hi < 0:
            status[idx] = IVStatus.OUT_OF_RANGE.value
            continue
        root, info = brentq(
            objective,
            lo,
            hi,
            xtol=settings.iv_tolerance,
            maxiter=settings.iv_max_iterations,
            full_output=True,
            disp=False,
        )
        if info.converged:
            iv[idx] = root
        else:
            status[idx] = IVStatus.NOT_CONVERGED.value
    return iv, status


def options_implied_vol(
    options: pd.DataFrame, risk_free_rate_annual: float, settings: PricingSettings
) -> pd.DataFrame:
    """IV sobre o mid de cada série de um snapshot (colunas de schema.OPTIONS_COLUMNS).

    Devolve DataFrame com o mesmo índice e colunas `t_years`, `rate`, `iv`, `iv_status`.
    """
    t = year_fraction(options["dte_business_days"].to_numpy())
    rate = continuous_rate(risk_free_rate_annual)
    iv, status = implied_volatility(
        options["mid"].to_numpy(dtype=np.float64),
        options["underlying_price"].to_numpy(dtype=np.float64),
        options["strike"].to_numpy(dtype=np.float64),
        t,
        rate,
        (options["option_type"] == "call").to_numpy(),
        settings,
    )
    return pd.DataFrame(
        {"t_years": t, "rate": float(rate), "iv": iv, "iv_status": status}, index=options.index
    )


def atm_implied_vol(series: pd.DataFrame, settings: PricingSettings) -> pd.DataFrame:
    """IV ATM por (underlying, expiration_date).

    Candidatas: IV válida, spread bid/ask ≤ atm_max_spread_pct_mid (book quebrado distorce a IV)
    e strike a no máximo atm_max_strike_distance_pct do spot. Para cada tipo (call e put) pega a
    candidata de strike mais próximo e faz a média; se só um tipo existir, usa esse. Vencimento
    sem candidata fica fora do resultado. Saída: underlying, expiration_date, atm_iv,
    atm_strike_distance_pct.
    """
    valid = series[
        (series["iv_status"] == IVStatus.OK.value)
        & (series["spread_pct_mid"] <= settings.atm_max_spread_pct_mid)
    ].assign(strike_distance_pct=lambda d: (d["strike"] / d["underlying_price"] - 1).abs())
    valid = valid[valid["strike_distance_pct"] <= settings.atm_max_strike_distance_pct]
    nearest = (
        valid.sort_values("strike_distance_pct")
        .groupby(["underlying", "expiration_date", "option_type"], sort=False)
        .head(1)
    )
    return (
        nearest.groupby(["underlying", "expiration_date"])
        .agg(atm_iv=("iv", "mean"), atm_strike_distance_pct=("strike_distance_pct", "max"))
        .reset_index()
    )
