"""DBSCAN exato em uma dimensao (secoes 14 e 15).

Em 1-D o DBSCAN pode ser resolvido com busca binaria em O(n log n), sem a
matriz de distancias do sklearn -- necessario porque o historico gera dezenas
de milhares de eventos.
"""

from __future__ import annotations

import numpy as np


def cluster_1d(x: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    """Rotula os pontos; -1 = ruido.

    Observacao pratica: em 1-D o DBSCAN encadeia com facilidade (efeito
    'corrente'), o que pode fundir toda a faixa de precos em um unico cluster
    quando os eventos sao densos. Por isso o metodo padrao do projeto e o KDE.
    """
    n = x.size
    labels = np.full(n, -1, dtype="int64")
    if n == 0:
        return labels

    order = np.argsort(x, kind="mergesort")
    xs = x[order]

    left = np.searchsorted(xs, xs - eps, side="left")
    right = np.searchsorted(xs, xs + eps, side="right")
    core = (right - left) >= min_samples

    sorted_labels = np.full(n, -1, dtype="int64")
    core_idx = np.flatnonzero(core)
    if core_idx.size == 0:
        return labels

    core_vals = xs[core_idx]
    new_cluster = np.diff(core_vals) > eps
    sorted_labels[core_idx] = np.concatenate([[0], np.cumsum(new_cluster)])

    # pontos de borda: nao-core a menos de eps de algum core
    border = np.flatnonzero(~core)
    if border.size:
        v = xs[border]
        j = np.searchsorted(core_vals, v)
        jl = np.clip(j - 1, 0, core_vals.size - 1)
        jr = np.clip(j, 0, core_vals.size - 1)
        dl = np.abs(v - core_vals[jl])
        dr = np.abs(v - core_vals[jr])
        pick = np.where(dl <= dr, jl, jr)
        dist = np.minimum(dl, dr)
        sorted_labels[border] = np.where(dist <= eps, sorted_labels[core_idx[pick]], -1)

    labels[order] = sorted_labels
    return labels
