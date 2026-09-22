"""Números no formato brasileiro para textos e gráficos do aviso."""

from __future__ import annotations

import math

MISSING = "—"


def num(value: float | None, decimals: int = 2) -> str:
    """1234.5 → '1.234,50'."""
    if value is None or not math.isfinite(value):
        return MISSING
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def brl(value: float | None, decimals: int = 2) -> str:
    """-12.5 → '−R$ 12,50'."""
    if value is None or not math.isfinite(value):
        return MISSING
    sign = "−" if value < 0 else ""
    return f"{sign}R$ {num(abs(value), decimals)}"


def pct(value: float | None, decimals: int = 1, signed: bool = False) -> str:
    """0.4038 → '40,4%'."""
    if value is None or not math.isfinite(value):
        return MISSING
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{num(value * 100, decimals)}%"
