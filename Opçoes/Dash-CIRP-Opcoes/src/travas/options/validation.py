"""Validação de travas verticais pelas pernas (não pelo rótulo escolhido)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from travas.options.models import (
    Direction,
    Flow,
    OptionType,
    Side,
    Structure,
    VerticalKind,
    vertical_kind,
)
from travas.options.payoff import MissingPriceError, expiry_profile, pnl_at_expiry

PRICE_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class VerticalValidation:
    kind: VerticalKind | None
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.kind is not None and not self.errors


def structural_kind(structure: Structure) -> tuple[VerticalKind | None, list[str]]:
    """Classifica pela geometria das pernas (sem olhar preços); erros se não for vertical."""
    errors: list[str] = []
    legs = structure.legs
    if len(legs) != 2:
        return None, [f"trava vertical exige 2 pernas, recebidas {len(legs)}"]
    a, b = legs
    if a.option_type is not b.option_type:
        errors.append("pernas de classes diferentes (call com put): não é trava vertical")
    if a.expiration != b.expiration:
        errors.append(
            "vencimentos diferentes: estrutura calendário/diagonal, "
            "fora do escopo de trava vertical"
        )
    if a.side is b.side:
        errors.append("as duas pernas no mesmo lado: trava exige uma compra e uma venda")
    if math.isclose(a.strike, b.strike):
        errors.append("strikes iguais: trava vertical exige strikes distintos")
    if a.strike <= 0 or b.strike <= 0:
        errors.append("strike não positivo")
    if a.quantity <= 0 or b.quantity <= 0:
        errors.append("quantidade deve ser positiva")
    if a.units != b.units:
        errors.append("quantidade × multiplicador diferente entre as pernas (trava desbalanceada)")
    if errors:
        return None, errors

    long_leg = a if a.side is Side.LONG else b
    short_leg = b if long_leg is a else a
    long_is_lower = long_leg.strike < short_leg.strike
    if a.option_type is OptionType.CALL:
        kind = VerticalKind.BULL_CALL_DEBIT if long_is_lower else VerticalKind.BEAR_CALL_CREDIT
    else:
        kind = VerticalKind.BULL_PUT_CREDIT if long_is_lower else VerticalKind.BEAR_PUT_DEBIT
    return kind, []


def validate_vertical(
    structure: Structure,
    expected_direction: Direction | None = None,
    expected_flow: Flow | None = None,
) -> VerticalValidation:
    """Confere geometria, sinal do fluxo de entrada e perfil de risco.

    - A geometria define a trava (ex.: call comprada no strike menor = alta com débito).
    - Com preços, o fluxo de entrada precisa ter o sinal esperado (débito/crédito) e ser menor que
      a largura; caso contrário a cotação está inconsistente (arbitragem aparente ou book ruim).
    - O perfil no vencimento precisa ser crescente (alta) ou decrescente (baixa) e limitado.
    """
    kind, errors = structural_kind(structure)
    if kind is None:
        return VerticalValidation(None, tuple(errors))

    warnings: list[str] = []
    if expected_direction is not None and expected_flow is not None:
        expected = vertical_kind(expected_direction, expected_flow)
        if expected is not kind:
            errors.append(f"pernas formam '{kind.label}', não '{expected.label}'")

    try:
        profile = expiry_profile(structure)
    except MissingPriceError as exc:
        warnings.append(f"sem preço de entrada: {exc}")
        return VerticalValidation(kind, tuple(errors), tuple(warnings))

    units = structure.legs[0].units
    width = abs(structure.legs[0].strike - structure.legs[1].strike)
    premium_per_unit = profile.net_premium / units
    if kind.flow is Flow.DEBIT and premium_per_unit >= -PRICE_TOLERANCE:
        errors.append("preços inconsistentes: esta trava deveria gerar débito na entrada")
    if kind.flow is Flow.CREDIT and premium_per_unit <= PRICE_TOLERANCE:
        errors.append("preços inconsistentes: esta trava deveria gerar crédito na entrada")
    if abs(premium_per_unit) >= width - PRICE_TOLERANCE:
        errors.append("fluxo de entrada ≥ largura da trava: sem lucro possível no vencimento")

    if not (math.isfinite(profile.max_profit) and math.isfinite(profile.max_loss)):
        errors.append("perfil de risco ilimitado: não é trava vertical")
    rising = profile.slope_right == 0 and _rises(structure)
    if kind.direction is Direction.BULL and not rising:
        errors.append("perfil não é de alta (P&L não cresce com o ativo)")
    if kind.direction is Direction.BEAR and rising:
        errors.append("perfil não é de baixa (P&L não cai com o ativo)")
    return VerticalValidation(kind, tuple(errors), tuple(warnings))


def _rises(structure: Structure) -> bool:
    """P&L acima do maior strike maior que abaixo do menor strike."""
    lo, hi = min(structure.strikes), max(structure.strikes)
    low, high = pnl_at_expiry(structure, [lo, hi])
    return bool(high > low)
