"""Agrupamento aglomerativo 1-D com diametro limitado (secao 14).

Equivalente ao complete-linkage cortado em `2*eps`, mas resolvido em tempo
linear explorando a ordenacao dos precos. Diferente do DBSCAN, garante que
nenhum cluster fique mais largo que a tolerancia -- nao ha encadeamento.
"""

from __future__ import annotations

import numpy as np


def cluster_1d(x: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    n = x.size
    labels = np.full(n, -1, dtype="int64")
    if n == 0:
        return labels

    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    width = 2.0 * eps

    sorted_labels = np.empty(n, dtype="int64")
    start = 0
    lab = 0
    while start < n:
        stop = int(np.searchsorted(xs, xs[start] + width, side="right"))
        sorted_labels[start:stop] = lab
        lab += 1
        start = stop

    # descarta clusters pouco povoados
    counts = np.bincount(sorted_labels, minlength=lab)
    sorted_labels = np.where(counts[sorted_labels] >= min_samples, sorted_labels, -1)

    labels[order] = sorted_labels
    return labels
