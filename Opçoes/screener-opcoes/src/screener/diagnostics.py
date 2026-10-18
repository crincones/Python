"""Diagnóstico dos campos expostos pela corretora (sem dependência do MT5)."""

from __future__ import annotations

import pandas as pd


def field_fill_rates(frame: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Percentual de linhas com valor não nulo e diferente de zero/vazio em cada campo.

    Zero é tratado como "ausente", conforme a convenção do projeto para campos do MT5.
    """
    rows = []
    for field in fields:
        column = frame[field]
        if pd.api.types.is_numeric_dtype(column):
            present = column.notna() & (column != 0)
        else:
            present = column.notna() & (column.astype(str).str.len() > 0)
        rows.append({"field": field, "filled": int(present.sum()), "total": len(column)})
    result = pd.DataFrame(rows, columns=["field", "filled", "total"])
    result["fill_rate"] = result["filled"] / result["total"].where(result["total"] > 0)
    return result
