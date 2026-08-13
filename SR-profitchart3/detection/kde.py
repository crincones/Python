"""Kernel Density Estimation sobre os eventos (secao 23).

A densidade e ponderada pela importancia do evento (forca da reacao, escala,
recencia e volume), nao pela simples contagem. Os maximos locais da densidade
sao os candidatos a nivel.

Como o historico do WIN percorre uma faixa ampla de precos (122k -> 168k), a
densidade e construida em espaco logaritmico: assim a banda acompanha a
volatilidade relativa em vez de ser um numero fixo de pontos.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


def density(
    x: np.ndarray,
    w: np.ndarray,
    bandwidth: float,
    grid_n: int = 20000,
) -> Tuple[np.ndarray, np.ndarray]:
    """Densidade gaussiana ponderada, avaliada em uma grade regular."""
    lo, hi = float(x.min()), float(x.max())
    pad = 3.0 * bandwidth
    grid = np.linspace(lo - pad, hi + pad, int(grid_n))
    step = grid[1] - grid[0]

    idx = np.clip(np.rint((x - grid[0]) / step).astype("int64"), 0, grid.size - 1)
    hist = np.bincount(idx, weights=w, minlength=grid.size).astype("float64")
    dens = gaussian_filter1d(hist, max(bandwidth / step, 1e-9), mode="constant")
    return grid, dens


def density_peaks(
    x: np.ndarray,
    w: np.ndarray,
    bandwidth: float,
    grid_n: int = 20000,
    prominence_frac: float = 0.02,
    min_distance: float = 0.0,
):
    """Maximos locais da densidade -> precos candidatos (em espaco de `x`)."""
    grid, dens = density(x, w, bandwidth, grid_n)
    if dens.max() <= 0:
        return np.array([]), grid, dens

    step = grid[1] - grid[0]
    distance = max(int(round(min_distance / step)), 1)
    peaks, _ = find_peaks(
        dens,
        prominence=prominence_frac * float(dens.max()),
        distance=distance,
    )
    return grid[peaks], grid, dens


def assign(x: np.ndarray, peaks: np.ndarray, radius: float) -> np.ndarray:
    """Atribui cada evento ao pico mais proximo dentro de `radius` (-1 = nenhum)."""
    n = x.size
    labels = np.full(n, -1, dtype="int64")
    if peaks.size == 0 or n == 0:
        return labels

    j = np.searchsorted(peaks, x)
    jl = np.clip(j - 1, 0, peaks.size - 1)
    jr = np.clip(j, 0, peaks.size - 1)
    dl = np.abs(x - peaks[jl])
    dr = np.abs(x - peaks[jr])
    pick = np.where(dl <= dr, jl, jr)
    dist = np.minimum(dl, dr)
    return np.where(dist <= radius, pick, -1)
