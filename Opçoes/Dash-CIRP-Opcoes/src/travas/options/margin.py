"""Garantia (margem) estimada de uma estrutura. Função pura, sem MT5.

A B3 calcula a margem pela metodologia CORE (cenários de estresse sobre a carteira inteira) e a
corretora pode exigir mais; nenhuma das duas é acessível via MT5. Aqui fica só uma **estimativa
pelo risco no vencimento**, com a metodologia exibida:

- obrigação = pior valor das pernas no vencimento sem os prêmios (o que as vendas podem custar
  além do que as compras cobrem). Trava de crédito: largura × unidades; trava de débito: zero.
- garantia estimada = obrigação − crédito recebido (o crédito fica na conta e cobre parte do
  risco). Numa trava vertical é a própria perda máxima (sem custos).
- garantia conservadora = obrigação inteira (corretora que não aceita o crédito como garantia).
- Venda descoberta de call (risco ilimitado) ou vencimentos diferentes: não estimável.
"""

from __future__ import annotations

import math

import numpy as np

from travas.options.models import OptionType, Side, Structure
from travas.options.payoff import ZERO_TOLERANCE, intrinsic, net_premium

METHOD = (
    "Estimativa pelo risco no vencimento: obrigação das pernas vendidas não coberta pelas "
    "compradas (pior caso, sem prêmios), menos o crédito recebido. A B3 calcula a margem "
    "real pela metodologia CORE e a corretora pode exigir mais; confira no home broker/"
    "ProfitChart antes de operar. Ações ou títulos em custódia podem servir de garantia."
)
STYLE_WARNING = (
    "perna vendida americana coberta por comprada europeia: num exercício antecipado a comprada "
    "não pode ser exercida para compensar, e a B3/corretora pode exigir garantia maior"
)


def obligation(structure: Structure) -> tuple[float, bool]:
    """(pior valor das pernas no vencimento sem prêmios, positivo = a pagar; ilimitado?)."""
    xs = np.array([0.0, *structure.strikes])
    value = np.zeros_like(xs)
    for leg in structure.legs:
        value = value + leg.side.sign * leg.units * intrinsic(leg, xs)
    slope_right = sum(
        leg.side.sign * leg.units
        for leg in structure.legs
        if leg.option_type in (OptionType.CALL, OptionType.STOCK)
    )
    if slope_right < -ZERO_TOLERANCE:
        return math.inf, True
    return max(0.0, -float(value.min())), False


def style_mismatch(structure: Structure) -> bool:
    """Vendida americana cuja proteção (comprada da mesma classe) é só europeia."""
    for short in structure.option_legs:
        if short.side is not Side.SHORT or short.exercise_style != "american":
            continue
        cover = [
            leg
            for leg in structure.option_legs
            if leg.side is Side.LONG and leg.option_type is short.option_type
        ]
        if cover and all(leg.exercise_style == "european" for leg in cover):
            return True
    return False


def margin_estimate(structure: Structure) -> dict:
    """Garantia estimada e conservadora (R$ totais) e o capital comprometido na entrada."""
    shorts = [leg for leg in structure.legs if leg.side is Side.SHORT]
    base = {"method": METHOD, "notes": [], "estimated": None, "conservative": None}
    if len(structure.expirations) > 1:
        return {
            **base,
            "available": False,
            "reason": "vencimentos diferentes: garantia depende da CORE (B3) após o 1º vencimento",
        }
    cash = net_premium(structure)
    credit, debit = max(cash, 0.0), max(-cash, 0.0)
    if not shorts:
        return {
            **base,
            "available": True,
            "reason": None,
            "estimated": 0.0,
            "conservative": 0.0,
            "obligation": 0.0,
            "credit": credit,
            "debit": debit,
            "capital_estimated": debit,
            "capital_conservative": debit,
            "notes": ["só posições compradas: sem garantia; o capital é o valor pago"],
        }
    owed, unbounded = obligation(structure)
    if unbounded:
        return {
            **base,
            "available": False,
            "reason": "venda descoberta (risco ilimitado na alta): garantia calculada pela B3 "
            "(CORE) e pela corretora, não estimável aqui",
        }
    estimated = max(0.0, owed - credit)
    notes = []
    if owed <= ZERO_TOLERANCE:
        notes.append("vendas cobertas pelas compras no vencimento: em geral sem garantia adicional")
    if style_mismatch(structure):
        notes.append(STYLE_WARNING)
    return {
        **base,
        "available": True,
        "reason": None,
        "estimated": estimated,
        "conservative": owed,
        "obligation": owed,
        "credit": credit,
        "debit": debit,
        "capital_estimated": debit + estimated,
        "capital_conservative": debit + owed,
        "notes": notes,
    }


def exit_spread_cost(
    units: list[float], bids: list[float | None], asks: list[float | None]
) -> float | None:
    """Custo de zerar pelo natural em vez do mid com o book atual: Σ unidades × (ask − bid)/2.
    None se faltar book em alguma perna."""
    total = 0.0
    for n, bid, ask in zip(units, bids, asks, strict=True):
        if bid is None or ask is None or ask < bid:
            return None
        total += n * (ask - bid) / 2
    return total
