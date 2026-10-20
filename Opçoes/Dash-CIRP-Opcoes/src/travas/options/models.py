"""Modelos de pernas e estruturas. Sem dependência de MT5 nem de interface."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, replace
from enum import StrEnum


class OptionType(StrEnum):
    CALL = "call"
    PUT = "put"
    STOCK = "ativo"  # o próprio ativo-objeto (simulador): valor = preço do ativo, sem strike


class Side(StrEnum):
    LONG = "compra"
    SHORT = "venda"

    @property
    def sign(self) -> int:
        """+1 para compra (posição comprada), −1 para venda."""
        return 1 if self is Side.LONG else -1


class Direction(StrEnum):
    BULL = "alta"
    BEAR = "baixa"


class Flow(StrEnum):
    DEBIT = "debito"
    CREDIT = "credito"


class VerticalKind(StrEnum):
    """As quatro travas verticais canônicas (mesma classe, mesmo vencimento)."""

    BULL_CALL_DEBIT = "alta_debito_call"
    BEAR_PUT_DEBIT = "baixa_debito_put"
    BULL_PUT_CREDIT = "alta_credito_put"
    BEAR_CALL_CREDIT = "baixa_credito_call"

    @property
    def direction(self) -> Direction:
        return VERTICAL_SPECS[self][0]

    @property
    def flow(self) -> Flow:
        return VERTICAL_SPECS[self][1]

    @property
    def option_type(self) -> OptionType:
        return VERTICAL_SPECS[self][2]

    @property
    def label(self) -> str:
        return VERTICAL_SPECS[self][3]


VERTICAL_SPECS: dict[VerticalKind, tuple[Direction, Flow, OptionType, str]] = {
    VerticalKind.BULL_CALL_DEBIT: (
        Direction.BULL,
        Flow.DEBIT,
        OptionType.CALL,
        "Trava de alta com débito (calls)",
    ),
    VerticalKind.BEAR_PUT_DEBIT: (
        Direction.BEAR,
        Flow.DEBIT,
        OptionType.PUT,
        "Trava de baixa com débito (puts)",
    ),
    VerticalKind.BULL_PUT_CREDIT: (
        Direction.BULL,
        Flow.CREDIT,
        OptionType.PUT,
        "Trava de alta com crédito (puts)",
    ),
    VerticalKind.BEAR_CALL_CREDIT: (
        Direction.BEAR,
        Flow.CREDIT,
        OptionType.CALL,
        "Trava de baixa com crédito (calls)",
    ),
}


def vertical_kind(direction: Direction, flow: Flow) -> VerticalKind:
    for kind, (d, f, _, _) in VERTICAL_SPECS.items():
        if d is direction and f is flow:
            return kind
    raise ValueError(f"combinação inválida: {direction}, {flow}")


@dataclass(frozen=True, slots=True)
class Leg:
    """Uma perna. `price` é o prêmio por unidade (por ação) usado na entrada.

    `quantity`: número de opções; `multiplier`: unidades do ativo por opção (trade_contract_size
    no MT5; 1 nas opções de ações da B3). Valor financeiro = preço × quantity × multiplier.
    """

    option_type: OptionType
    side: Side
    strike: float
    expiration: dt.date
    quantity: int
    multiplier: float
    price: float | None
    symbol: str | None = None
    exercise_style: str | None = None

    @property
    def units(self) -> float:
        return self.quantity * self.multiplier

    def with_price(self, price: float | None) -> Leg:
        return replace(self, price=price)


@dataclass(frozen=True, slots=True)
class Structure:
    underlying: str
    legs: tuple[Leg, ...]

    def with_prices(self, prices: list[float | None]) -> Structure:
        if len(prices) != len(self.legs):
            raise ValueError("um preço por perna")
        return replace(
            self, legs=tuple(leg.with_price(p) for leg, p in zip(self.legs, prices, strict=True))
        )

    @property
    def option_legs(self) -> tuple[Leg, ...]:
        return tuple(leg for leg in self.legs if leg.option_type is not OptionType.STOCK)

    @property
    def strikes(self) -> list[float]:
        return sorted({leg.strike for leg in self.option_legs})

    @property
    def expirations(self) -> set[dt.date]:
        return {leg.expiration for leg in self.option_legs}
