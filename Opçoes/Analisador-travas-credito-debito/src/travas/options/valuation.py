"""Valor teórico da estrutura antes do vencimento (Black-Scholes europeu por perna).

Premissas (exibidas na interface): σ constante por perna até a data simulada, taxa livre de
risco constante, sem dividendos, exercício europeu, T em dias úteis/252. No dia do vencimento o
valor converge para o payoff exato. Calls americanas sem proventos valem como europeias; puts
americanas e ativos com provento antes do vencimento ficam aproximados.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike

from travas.options import pricing
from travas.options.models import OptionType, Structure
from travas.options.payoff import ZERO_TOLERANCE, FloatArray, net_premium


def _per_leg(t_years: float | Sequence[float], n: int) -> list[float]:
    """Prazo único para todas as pernas ou um prazo por perna (vencimentos diferentes)."""
    if isinstance(t_years, int | float):
        return [float(t_years)] * n
    values = [float(t) for t in t_years]
    if len(values) != n:
        raise ValueError("um prazo por perna")
    return values


def structure_value(
    structure: Structure,
    spot: ArrayLike,
    t_years: float | Sequence[float],
    rate: float,
    sigmas: Sequence[float | None],
) -> FloatArray:
    """Valor de mercado teórico da posição (R$ totais, comprado +, vendido −).

    `t_years` pode ser um prazo por perna. Perna com prazo ≤ 0 vale o intrínseco (não usa σ).
    """
    s = np.asarray(spot, dtype=np.float64)
    value = np.zeros_like(s)
    terms = _per_leg(t_years, len(structure.legs))
    for leg, sigma, t in zip(structure.legs, sigmas, terms, strict=True):
        premium = pricing.price(
            s,
            leg.strike,
            t,
            rate,
            np.nan if sigma is None else sigma,
            leg.option_type is OptionType.CALL,
        )
        value = value + leg.side.sign * leg.units * premium
    return value


def theoretical_pnl(
    structure: Structure,
    spot: ArrayLike,
    t_years: float | Sequence[float],
    rate: float,
    sigmas: Sequence[float | None],
    costs: float = 0.0,
) -> FloatArray:
    """P&L teórico se a posição fosse zerada pelo valor do modelo na data com prazo `t_years`."""
    return structure_value(structure, spot, t_years, rate, sigmas) + net_premium(structure) - costs


def structure_greeks(
    structure: Structure,
    spot: float,
    t_years: float | Sequence[float],
    rate: float,
    sigmas: Sequence[float],
) -> dict[str, float]:
    """Gregas da posição (R$ totais). Theta por dia útil; vega e rho por 1 p.p."""
    total = {
        "delta": 0.0,
        "gamma": 0.0,
        "theta_per_day": 0.0,
        "vega_per_pp": 0.0,
        "rho_per_pp": 0.0,
    }
    terms = _per_leg(t_years, len(structure.legs))
    for leg, sigma, t in zip(structure.legs, sigmas, terms, strict=True):
        g = pricing.greeks(spot, leg.strike, t, rate, sigma, leg.option_type is OptionType.CALL)
        k = leg.side.sign * leg.units
        total["delta"] += k * float(g["delta"])
        total["gamma"] += k * float(g["gamma"])
        total["theta_per_day"] += k * float(g["theta"]) / pricing.BUSINESS_DAYS_PER_YEAR
        total["vega_per_pp"] += k * float(g["vega"]) / 100
        total["rho_per_pp"] += k * float(g["rho"]) / 100
    return total


def zero_crossings(xs: FloatArray, ys: FloatArray) -> list[float]:
    """Raízes por interpolação linear numa curva amostrada (equilíbrio em data simulada)."""
    roots: list[float] = []
    for i in range(len(xs) - 1):
        a, b = ys[i], ys[i + 1]
        if abs(a) <= ZERO_TOLERANCE:
            roots.append(float(xs[i]))
        elif a * b < 0:
            roots.append(float(xs[i] + (xs[i + 1] - xs[i]) * (-a) / (b - a)))
    if len(ys) and abs(ys[-1]) <= ZERO_TOLERANCE:
        roots.append(float(xs[-1]))
    return sorted({round(r, 6) for r in roots})


def valid_sigmas(sigmas: Sequence[float | None]) -> bool:
    return all(s is not None and math.isfinite(s) and s > 0 for s in sigmas)
