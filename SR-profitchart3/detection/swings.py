"""Deteccao de swing points (secao 12).

Swing high e swing low NAO produzem tipos diferentes de nivel: ambos geram
apenas `candidate level`. A direcao e usada somente para saber qual preco da
barra representa a interacao.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view


def _local_extreme_mask(values: np.ndarray, n: int, maximum: bool) -> np.ndarray:
    """True nas posicoes que sao extremo local de uma janela de 2n+1 barras."""
    size = 2 * n + 1
    mask = np.zeros(values.size, dtype=bool)
    if values.size < size:
        return mask
    win = sliding_window_view(values, size)
    hit = (win.argmax(axis=1) if maximum else win.argmin(axis=1)) == n
    mask[n:values.size - n] = hit
    return mask


def find_swings(bars: pd.DataFrame, n: int) -> pd.DataFrame:
    """Devolve os swings de uma escala.

    Colunas: timestamp, bar (posicao na serie da escala), pos (minuto do extremo
    na serie de 1m), price_extreme, price_close, price_mid.
    """
    if bars.empty:
        return pd.DataFrame(columns=["timestamp", "bar", "pos", "price_extreme",
                                     "price_close", "price_mid"])

    high = bars["high"].to_numpy()
    low = bars["low"].to_numpy()
    is_hi = _local_extreme_mask(high, n, True)
    is_lo = _local_extreme_mask(low, n, False)

    frames = []
    for mask, price_col, pos_col in ((is_hi, "high", "hi_pos"), (is_lo, "low", "lo_pos")):
        if not mask.any():
            continue
        sub = bars.loc[mask]
        frames.append(pd.DataFrame({
            "timestamp": sub.index,
            "bar": np.flatnonzero(mask),
            "pos": sub[pos_col].to_numpy(),
            "price_extreme": sub[price_col].to_numpy(),
            "price_close": sub["close"].to_numpy(),
            "price_mid": (sub["high"].to_numpy() + sub["low"].to_numpy()) / 2.0,
        }))

    if not frames:
        return pd.DataFrame(columns=["timestamp", "bar", "pos", "price_extreme",
                                     "price_close", "price_mid"])

    out = pd.concat(frames, ignore_index=True)
    return out.sort_values("pos", kind="mergesort").reset_index(drop=True)
