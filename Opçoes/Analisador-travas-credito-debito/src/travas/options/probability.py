"""Probabilidades sob modelo lognormal (movimento browniano geométrico). Funções puras.

Metodologia (exibida na interface junto de cada número):
- ln(S_T / S_0) ~ Normal((μ − σ²/2)·T, σ²·T), com T em anos de dias úteis (du/252).
- μ = taxa livre de risco contínua (medida neutra ao risco), salvo indicação contrária. Não é uma
  previsão do mercado: é a hipótese padrão de precificação.
- σ = volatilidade implícita ATM do vencimento (calculada sobre o mid) ou informada pelo usuário.
- POP = probabilidade de o P&L **no vencimento** ser > 0 (custos incluídos quando informados).
  Não é a probabilidade de lucro em algum momento antes do vencimento.
- Probabilidade de toque = probabilidade de o preço atingir um nível em algum momento até T
  (princípio da reflexão para o MBG, monitoramento contínuo; o pregão real é discreto).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.special import ndtr

from travas.options.models import Structure
from travas.options.payoff import profit_intervals

POP_METHOD = (
    "Lognormal (Black-Scholes), drift = taxa livre de risco, σ = {vol_source}, "
    "T = dias úteis/252. Probabilidade de lucro no vencimento, não antes dele."
)


@dataclass(frozen=True, slots=True)
class Probability:
    value: float | None
    method: str
    reason: str | None = None  # motivo quando value é None


def _valid(spot: float, t: float, sigma: float | None) -> str | None:
    if not (spot > 0 and math.isfinite(spot)):
        return "preço do ativo-objeto ausente"
    if not (t > 0):
        return "sem prazo até o vencimento"
    if sigma is None or not math.isfinite(sigma) or sigma <= 0:
        return "volatilidade indisponível ou não confiável"
    return None


def prob_below(spot: float, level: float, t: float, drift: float, sigma: float) -> float:
    """P(S_T < level)."""
    if level <= 0:
        return 0.0
    if math.isinf(level):
        return 1.0
    z = (math.log(level / spot) - (drift - 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    return float(ndtr(z))


def prob_between(spot: float, lo: float, hi: float, t: float, drift: float, sigma: float) -> float:
    return max(0.0, prob_below(spot, hi, t, drift, sigma) - prob_below(spot, lo, t, drift, sigma))


def pop_at_expiry(
    structure: Structure,
    spot: float,
    t: float,
    drift: float,
    sigma: float | None,
    vol_source: str,
    costs: float = 0.0,
) -> Probability:
    method = POP_METHOD.format(vol_source=vol_source)
    if (problem := _valid(spot, t, sigma)) is not None:
        return Probability(None, method, problem)
    assert sigma is not None
    total = sum(
        prob_between(spot, lo, hi, t, drift, sigma) for lo, hi in profit_intervals(structure, costs)
    )
    return Probability(min(1.0, total), method)


def prob_finish_beyond(
    spot: float, level: float, above: bool, t: float, drift: float, sigma: float | None
) -> Probability:
    """P(S_T ≥ level) se `above`, senão P(S_T ≤ level)."""
    method = "Lognormal no vencimento (drift = taxa livre de risco)"
    if (problem := _valid(spot, t, sigma)) is not None:
        return Probability(None, method, problem)
    assert sigma is not None
    below = prob_below(spot, level, t, drift, sigma)
    return Probability(1.0 - below if above else below, method)


def prob_touch(
    spot: float, level: float, t: float, drift: float, sigma: float | None
) -> Probability:
    """P(o preço atingir `level` em algum momento até T) — princípio da reflexão (MBG)."""
    method = "Toque antes do vencimento: MBG, monitoramento contínuo (aproximação)"
    if (problem := _valid(spot, t, sigma)) is not None:
        return Probability(None, method, problem)
    assert sigma is not None
    if level <= 0:
        return Probability(None, method, "nível inválido")
    nu = drift - 0.5 * sigma * sigma
    x = math.log(level / spot)
    sd = sigma * math.sqrt(t)
    if x == 0:
        return Probability(1.0, method)
    if x > 0:  # barreira acima
        p = ndtr((-x + nu * t) / sd) + math.exp(2 * nu * x / sigma**2) * ndtr((-x - nu * t) / sd)
    else:  # barreira abaixo
        p = ndtr((x - nu * t) / sd) + math.exp(2 * nu * x / sigma**2) * ndtr((x + nu * t) / sd)
    return Probability(float(min(1.0, max(0.0, p))), method)
