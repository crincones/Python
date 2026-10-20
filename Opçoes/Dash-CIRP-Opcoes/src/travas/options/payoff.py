"""Payoff no vencimento, risco, lucro e breakevens. Funções puras e genéricas por pernas.

Convenções:
- Resultado (P&L) em R$ totais da estrutura: Σ sinal × unidades × valor intrínseco + fluxo inicial
  − custos. Sinal +1 = compra, −1 = venda; unidades = quantidade × multiplicador.
- Fluxo inicial (`net_premium`) > 0 é crédito recebido; < 0 é débito pago.
- O payoff é linear por partes com quebras nos strikes; extremos e breakevens são calculados
  exatamente a partir dos pontos de quebra e das inclinações nas pontas (não por amostragem).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from travas.options.models import Leg, OptionType, Structure

FloatArray = NDArray[np.float64]
ZERO_TOLERANCE = 1e-9


class MissingPriceError(ValueError):
    """Alguma perna não tem preço de entrada."""


def intrinsic(leg: Leg, spot: ArrayLike) -> FloatArray:
    """Valor intrínseco por unidade no vencimento (perna de ativo: o próprio preço)."""
    s = np.asarray(spot, dtype=np.float64)
    if leg.option_type is OptionType.STOCK:
        return s.copy()
    if leg.option_type is OptionType.CALL:
        return np.maximum(s - leg.strike, 0.0)
    return np.maximum(leg.strike - s, 0.0)


def net_premium(structure: Structure) -> float:
    """Fluxo de caixa na entrada (R$ totais): positivo = crédito, negativo = débito."""
    total = 0.0
    for leg in structure.legs:
        if leg.price is None or not math.isfinite(leg.price):
            raise MissingPriceError(f"perna {leg.symbol or leg.strike} sem preço de entrada")
        total -= leg.side.sign * leg.price * leg.units
    return total


def pnl_at_expiry(structure: Structure, spot: ArrayLike, costs: float = 0.0) -> FloatArray:
    """Resultado total no vencimento para cada preço do ativo-objeto."""
    s = np.asarray(spot, dtype=np.float64)
    value = np.zeros_like(s)
    for leg in structure.legs:
        value = value + leg.side.sign * leg.units * intrinsic(leg, s)
    return value + net_premium(structure) - costs


def leg_pnl_at_expiry(leg: Leg, spot: ArrayLike) -> FloatArray:
    """Resultado de uma perna isolada no vencimento (inclui o prêmio pago/recebido)."""
    if leg.price is None:
        raise MissingPriceError(f"perna {leg.symbol or leg.strike} sem preço de entrada")
    return leg.side.sign * leg.units * (intrinsic(leg, spot) - leg.price)


@dataclass(frozen=True, slots=True)
class ExpiryProfile:
    """Perfil no vencimento, em R$ totais. `max_loss` é positivo quando há perda possível;
    `math.inf` indica perda ou lucro ilimitado."""

    net_premium: float
    max_profit: float
    max_loss: float
    breakevens: tuple[float, ...]
    slope_right: float  # variação do P&L por R$ 1 de alta do ativo acima do maior strike
    slope_left: float  # variação do P&L por R$ 1 de alta do ativo abaixo do menor strike

    @property
    def reward_risk(self) -> float:
        """Lucro máximo / perda máxima (NaN se indefinido)."""
        return _ratio(self.max_profit, self.max_loss)

    @property
    def risk_reward(self) -> float:
        """Perda máxima / lucro máximo (NaN se indefinido)."""
        return _ratio(self.max_loss, self.max_profit)


def _ratio(num: float, den: float) -> float:
    if not (math.isfinite(num) and math.isfinite(den)) or den <= 0:
        return math.nan
    return num / den


def expiry_profile(structure: Structure, costs: float = 0.0) -> ExpiryProfile:
    xs = np.array([0.0, *structure.strikes])
    values = pnl_at_expiry(structure, xs, costs)
    stock = sum(
        leg.side.sign * leg.units for leg in structure.legs if leg.option_type is OptionType.STOCK
    )
    slope_right = stock + sum(
        leg.side.sign * leg.units for leg in structure.legs if leg.option_type is OptionType.CALL
    )
    slope_left = stock - sum(
        leg.side.sign * leg.units for leg in structure.legs if leg.option_type is OptionType.PUT
    )

    best, worst = float(values.max()), float(values.min())
    max_profit = math.inf if slope_right > ZERO_TOLERANCE else best
    max_loss = math.inf if slope_right < -ZERO_TOLERANCE else -worst
    return ExpiryProfile(
        net_premium=net_premium(structure),
        max_profit=max_profit,
        max_loss=max_loss,
        breakevens=tuple(_breakevens(xs, values, slope_right)),
        slope_right=float(slope_right),
        slope_left=float(slope_left),
    )


def _breakevens(xs: FloatArray, values: FloatArray, slope_right: float) -> list[float]:
    """Preços em que o P&L cruza (ou toca, mudando de sinal) o zero."""
    roots: list[float] = []
    signs = np.sign(np.where(np.abs(values) <= ZERO_TOLERANCE, 0.0, values))
    for i in range(len(xs) - 1):
        a, b = values[i], values[i + 1]
        if signs[i] * signs[i + 1] < 0:
            roots.append(float(xs[i] + (xs[i + 1] - xs[i]) * (-a) / (b - a)))
    # Toques exatos em pontos de quebra: só contam se o sinal muda de um lado para o outro.
    extended = [*signs.tolist(), float(np.sign(slope_right)) if signs[-1] == 0 else signs[-1]]
    for i in range(1, len(xs)):
        if signs[i] != 0:
            continue
        left = next((s for s in reversed(extended[:i]) if s != 0), 0.0)
        right = next((s for s in extended[i + 1 :] if s != 0), 0.0)
        if left * right < 0:
            roots.append(float(xs[i]))
    last = values[-1]
    if signs[-1] != 0 and abs(slope_right) > ZERO_TOLERANCE and np.sign(slope_right) != signs[-1]:
        roots.append(float(xs[-1] - last / slope_right))
    return sorted(roots)


def profit_intervals(structure: Structure, costs: float = 0.0) -> list[tuple[float, float]]:
    """Intervalos de preço no vencimento com P&L > 0 (fim = inf quando ilimitado)."""
    profile = expiry_profile(structure, costs)
    edges = [0.0, *profile.breakevens, math.inf]
    intervals: list[tuple[float, float]] = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        if hi <= lo:
            continue
        probe = (lo + hi) / 2 if math.isfinite(hi) else lo + max(1.0, lo)
        if float(pnl_at_expiry(structure, [probe], costs)[0]) > ZERO_TOLERANCE:
            intervals.append((lo, hi))
    return intervals
