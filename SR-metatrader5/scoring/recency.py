"""Recencia (secao 20).

A recencia pesa, mas nao apaga o passado: o decaimento tem um piso. Como o
score usa a SOMA dos pesos decaidos, um nivel antigo que volta a ser testado
recupera relevancia sozinho.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def age_days(timestamps: pd.Series, ref_time: pd.Timestamp) -> np.ndarray:
    return np.maximum((ref_time - timestamps).dt.total_seconds().to_numpy() / 86400.0, 0.0)


def decay(age: np.ndarray, half_life_days: float, floor: float = 0.0) -> np.ndarray:
    """exp(-idade / meia_vida), limitado inferiormente por `floor`."""
    d = np.exp(-np.asarray(age, dtype="float64") / max(half_life_days, 1e-9))
    return floor + (1.0 - floor) * d
