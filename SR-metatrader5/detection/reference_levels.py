"""Niveis de referencia de mercado (secao 24).

Maxima/minima/abertura/fechamento de dia, semana e mes alimentam exatamente o
mesmo pipeline de eventos -- nao geram linhas proprias.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def reference_events(bars: pd.DataFrame, kinds) -> pd.DataFrame:
    """Converte barras de uma escala de referencia em eventos candidatos."""
    if bars.empty:
        return pd.DataFrame(columns=["pos", "price", "kind"])

    mapping = {
        "high": ("high", "hi_pos"),
        "low": ("low", "lo_pos"),
        "close": ("close", "last_pos"),
        "open": ("open", "first_pos"),
    }
    frames = []
    for kind in kinds:
        if kind not in mapping:
            continue
        price_col, pos_col = mapping[kind]
        frames.append(pd.DataFrame({
            "pos": bars[pos_col].to_numpy(),
            "price": bars[price_col].to_numpy(),
            "kind": kind,
        }))

    if not frames:
        return pd.DataFrame(columns=["pos", "price", "kind"])

    out = pd.concat(frames, ignore_index=True)
    return out.sort_values("pos", kind="mergesort").reset_index(drop=True)
