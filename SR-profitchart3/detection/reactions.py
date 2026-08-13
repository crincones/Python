"""Medicao da reacao posterior a um evento (secoes 10 e 11).

A reacao e direcionalmente neutra: mede-se apenas o quanto o preco se afastou
do nivel depois da interacao, para cima OU para baixo.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def forward_extremes(high: np.ndarray, low: np.ndarray, horizon: int):
    """Maxima e minima das `horizon` barras seguintes (exclui a barra atual)."""
    n = high.size
    fmax = np.full(n, np.nan)
    fmin = np.full(n, np.nan)
    if n < 2:
        return fmax, fmin

    rev_max = pd.Series(high[1:][::-1]).rolling(horizon, min_periods=1).max().to_numpy()[::-1]
    rev_min = pd.Series(low[1:][::-1]).rolling(horizon, min_periods=1).min().to_numpy()[::-1]
    fmax[:-1] = rev_max
    fmin[:-1] = rev_min
    return fmax, fmin


def build_excursion_tables(df: pd.DataFrame, horizons: List[int]) -> Dict[int, tuple]:
    """Pre-calcula, uma unica vez, as excursoes futuras para cada horizonte."""
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    return {h: forward_extremes(high, low, h) for h in horizons}


def measure(
    pos: np.ndarray,
    price: np.ndarray,
    tables: Dict[int, tuple],
    atr_ref: np.ndarray,
    ref_minutes: float,
):
    """Reacao e forca normalizada de cada evento.

    A reacao bruta e `max(maior alta acima do nivel, maior queda abaixo do nivel)`
    no horizonte. Para comparar horizontes diferentes, cada uma e dividida pelo
    movimento esperado `ATR_ref * sqrt(h / minutos_da_escala_ref)`; a forca do
    evento e o maior desses valores.
    """
    pos = np.asarray(pos, dtype="int64")
    price = np.asarray(price, dtype="float64")
    atr_e = atr_ref[pos]

    best_strength = np.zeros(price.size)
    best_reaction = np.zeros(price.size)
    per_horizon = {}

    for h, (fmax, fmin) in tables.items():
        # fmax e np.fmax: ignora NaN aos pares (fim da serie, sem futuro)
        react = np.fmax(fmax[pos] - price, price - fmin[pos])
        react = np.where(np.isfinite(react), np.maximum(react, 0.0), 0.0)
        expected = atr_e * np.sqrt(max(h, 1) / max(ref_minutes, 1.0))
        strength = react / np.where(expected > 0, expected, np.nan)
        strength = np.where(np.isfinite(strength), strength, 0.0)

        per_horizon[h] = (react, strength)
        upd = strength > best_strength
        best_strength = np.where(upd, strength, best_strength)
        best_reaction = np.where(upd, react, best_reaction)

    return best_reaction, best_strength, per_horizon
