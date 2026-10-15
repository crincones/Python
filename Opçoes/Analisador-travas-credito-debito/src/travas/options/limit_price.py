"""Preço de mercado, preço teórico e preço-limite sugerido de uma trava vertical.

Convenção: valores por unidade (por ação), sempre positivos, no sentido da estrutura —
"débito a pagar" nas travas de débito e "crédito a receber" nas de crédito.

- Natural: cruza o book em cada perna (compra no ask, venda no bid). É o pior preço "visível".
- Mid: mid da compra − mid da venda (ou o inverso no crédito). Só referência, sem garantia.
- Teórico: Black-Scholes com as premissas informadas.
- Sugerido: mid + agressividade × (natural − mid), arredondado ao tick no sentido favorável ao
  usuário (débito para baixo, crédito para cima), respeitando relação lucro/perda mínima e
  orçamento de perda quando informados. O ProfitChart recebe o preço manualmente.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from travas.options.models import Flow, Side, Structure
from travas.options.payoff import expiry_profile

TICK = 0.01


@dataclass(frozen=True, slots=True)
class PriceImpact:
    price: float
    max_profit: float  # R$ totais
    max_loss: float
    breakevens: tuple[float, ...]
    reward_risk: float


@dataclass(frozen=True, slots=True)
class LimitPrice:
    flow: Flow
    natural: float | None
    mid: float | None
    theoretical: float | None
    suggested: float | None
    range_low: float | None
    range_high: float | None
    impacts: dict[str, PriceImpact] = field(default_factory=dict)
    notes: tuple[str, ...] = ()
    reason_unavailable: str | None = None


def with_entry(structure: Structure, entry: float, flow: Flow) -> Structure:
    """Mesma trava com o fluxo de entrada por unidade fixado em `entry` (ajusta a perna comprada,
    mantendo a vendida)."""
    long_i = next(i for i, lg in enumerate(structure.legs) if lg.side is Side.LONG)
    short = next(lg for lg in structure.legs if lg.side is Side.SHORT)
    short_price = short.price if short.price is not None else 0.0
    long_price = short_price + entry if flow is Flow.DEBIT else short_price - entry
    prices = [lg.price for lg in structure.legs]
    prices[long_i] = long_price
    return structure.with_prices(prices)


def impact(structure: Structure, entry: float, flow: Flow, costs: float = 0.0) -> PriceImpact:
    profile = expiry_profile(with_entry(structure, entry, flow), costs)
    return PriceImpact(
        entry, profile.max_profit, profile.max_loss, profile.breakevens, profile.reward_risk
    )


def _round_favorable(value: float, flow: Flow) -> float:
    steps = value / TICK
    rounded = math.floor(steps + 1e-9) if flow is Flow.DEBIT else math.ceil(steps - 1e-9)
    return round(rounded * TICK, 2)


def suggest_limit(
    structure: Structure,
    flow: Flow,
    width: float,
    natural: float | None,
    mid: float | None,
    theoretical: float | None,
    aggressiveness: float,
    min_reward_risk: float | None = None,
    max_loss_total: float | None = None,
    costs: float = 0.0,
) -> LimitPrice:
    if natural is None or mid is None or not (math.isfinite(natural) and math.isfinite(mid)):
        return LimitPrice(
            flow,
            natural,
            mid,
            theoretical,
            None,
            None,
            None,
            reason_unavailable="não estimável: falta bid/ask válido em alguma perna",
        )
    notes: list[str] = []
    units = structure.legs[0].units
    raw = mid + aggressiveness * (natural - mid)
    suggested = _round_favorable(raw, flow)

    # Limites do usuário, convertidos em preço máximo (débito) ou mínimo (crédito).
    if min_reward_risk is not None and min_reward_risk > 0:
        bound = (
            width / (1 + min_reward_risk)
            if flow is Flow.DEBIT
            else width * min_reward_risk / (1 + min_reward_risk)
        )
        suggested = _apply_bound(
            suggested, _round_favorable(bound, flow), flow, notes, "lucro/perda mínima"
        )
    if max_loss_total is not None and max_loss_total > 0:
        per_unit = (max_loss_total - costs) / units
        bound = per_unit if flow is Flow.DEBIT else width - per_unit
        suggested = _apply_bound(
            suggested, _round_favorable(bound, flow), flow, notes, "perda máxima do orçamento"
        )

    if suggested <= 0 or suggested >= width:
        return LimitPrice(
            flow,
            natural,
            mid,
            theoretical,
            None,
            mid,
            natural,
            notes=tuple(notes),
            reason_unavailable=(
                "não estimável: limites do usuário incompatíveis com a largura da trava"
            ),
        )
    worse_than_mid = suggested > mid if flow is Flow.DEBIT else suggested < mid
    better_than_mid = suggested < mid if flow is Flow.DEBIT else suggested > mid
    if better_than_mid:
        notes.append("preço sugerido melhor que o mid: execução pouco provável")
    if not worse_than_mid and not better_than_mid:
        notes.append("preço sugerido no mid")
    notes.append("referência indicativa; execução não garantida")

    impacts = {"sugerido": impact(structure, suggested, flow, costs)}
    for name, value in (("mid", mid), ("natural", natural), ("teorico", theoretical)):
        if value is not None and math.isfinite(value) and 0 < value < width:
            impacts[name] = impact(structure, value, flow, costs)
    low, high = sorted((mid, natural))
    return LimitPrice(flow, natural, mid, theoretical, suggested, low, high, impacts, tuple(notes))


def _apply_bound(price: float, bound: float, flow: Flow, notes: list[str], label: str) -> float:
    if flow is Flow.DEBIT and price > bound:
        notes.append(f"limitado por {label}: débito máximo {bound:.2f}")
        return bound
    if flow is Flow.CREDIT and price < bound:
        notes.append(f"limitado por {label}: crédito mínimo {bound:.2f}")
        return bound
    return price
