"""Registro de estruturas acompanhadas (qualquer combinação de opções do mesmo ativo).

Preço de entrada: o usuário pode informar
- o **preço líquido** da estrutura por unidade (como o ProfitChart mostra para estratégias),
  com o sentido (débito pago / crédito recebido) — basta para o P&L total quando todas as pernas
  têm a mesma quantidade e são abertas/fechadas juntas; e/ou
- o **preço de cada perna** — necessário para P&L por perna, estruturas desbalanceadas
  (ex.: 1×2) e para registrar pernas montadas em momentos diferentes.
Se ambos vierem, os preços das pernas prevalecem e a diferença é sinalizada.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from travas.options.models import Flow, Side

MAX_LEGS = 8


class LegIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=32)
    side: Side
    quantity: int = Field(gt=0)
    entry_price: float | None = Field(default=None, ge=0)

    @field_validator("symbol")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class PositionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="", max_length=120)
    group: str = Field(default="Sem grupo", max_length=80)
    underlying: str = Field(min_length=1, max_length=16)
    legs: list[LegIn] = Field(min_length=1, max_length=MAX_LEGS)
    entry_net: float | None = Field(default=None, ge=0)  # por unidade, sempre positivo
    entry_flow: Flow | None = None  # débito pago ou crédito recebido
    entry_date: dt.date
    costs_entry: float = Field(default=0.0, ge=0)  # corretagem/emolumentos da entrada (R$)
    take_profit_pct: float | None = Field(default=None, gt=0, le=100)  # % do lucro máximo
    stop_loss_brl: float | None = Field(default=None, gt=0)  # prejuízo total que dispara alerta
    notes: str = Field(default="", max_length=2000)

    @field_validator("underlying", "group")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def _entry(self) -> PositionIn:
        self.underlying = self.underlying.upper()
        self.group = self.group or "Sem grupo"
        all_leg_prices = all(leg.entry_price is not None for leg in self.legs)
        if not all_leg_prices and self.entry_net is None:
            raise ValueError(
                "informe o preço líquido da estrutura ou o preço de entrada de todas as pernas"
            )
        if self.entry_net is not None and self.entry_flow is None:
            raise ValueError("informe se o preço líquido foi débito (pago) ou crédito (recebido)")
        if not all_leg_prices and len({leg.quantity for leg in self.legs}) > 1:
            raise ValueError(
                "pernas com quantidades diferentes: informe o preço de entrada de cada perna "
                "(o preço líquido por unidade fica ambíguo)"
            )
        return self


class ExitIn(BaseModel):
    """Encerramento total da estrutura (encerramento parcial: editar quantidades e registrar a
    parte encerrada como outra estrutura encerrada)."""

    model_config = ConfigDict(extra="forbid")

    exit_date: dt.date
    exit_net: float | None = Field(default=None, ge=0)
    exit_flow: Flow | None = None  # crédito recebido ao zerar ou débito pago ao zerar
    leg_prices: list[float | None] | None = None
    costs_exit: float = Field(default=0.0, ge=0)
    reason: Literal["zerada", "vencida", "exercida"] = "zerada"

    @model_validator(mode="after")
    def _price(self) -> ExitIn:
        has_legs = self.leg_prices is not None and all(p is not None for p in self.leg_prices)
        if not has_legs and (self.exit_net is None or self.exit_flow is None):
            raise ValueError("informe o preço líquido de saída (e o sentido) ou o de cada perna")
        return self
