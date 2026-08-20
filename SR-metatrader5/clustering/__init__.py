"""Interface unica de agrupamento de eventos por proximidade de preco."""

from __future__ import annotations

from typing import Tuple

import numpy as np

from clustering import dbscan, hierarchical
from detection import kde


def _transform(prices: np.ndarray, space: str) -> np.ndarray:
    """Espaco de trabalho do agrupamento.

    * `linear`: a tolerancia e absoluta, em pontos -- correto quando a unidade
      de estrutura e fixa (a caixa do Renko mede sempre 245 pts).
    * `log`: a tolerancia e relativa, em fracao do preco -- correto quando ela
      vem do ATR e o ativo percorreu patamares muito diferentes.
    """
    return prices if space == "linear" else np.log(prices)


def _cluster_grade(x: np.ndarray, step: float, min_samples: int):
    """Cada linha da grade e um nivel -- agrupamento nativo do Renko.

    Nao ha suavizacao nem tolerancia: os giros ja nascem sobre a grade, entao
    contar quantos caem em cada linha e a leitura mais direta possivel do
    grafico. Diferente do KDE, nao existe filtro global de proeminencia: uma
    linha muito testada nao apaga as outras so por estar em outro patamar de
    preco.
    """
    keys = np.round(x / step)
    vals, labels = np.unique(keys, return_inverse=True)
    counts = np.bincount(labels)
    labels = np.where(counts[labels] >= min_samples, labels, -1)
    return labels, vals * step


def cluster_events(
    prices: np.ndarray,
    weights: np.ndarray,
    cfg,
    band: float,
    min_distance: float = 0.0,
    space: str = None,
    grid_step: float = 0.0,
) -> Tuple[np.ndarray, dict]:
    """Agrupa eventos e devolve (labels, diagnostico).

    `band` e `min_distance` vem na mesma unidade do espaco escolhido: pontos no
    espaco linear, fracao do preco no espaco log.
    """
    space = space or getattr(cfg, "cluster_space", "log")
    x = _transform(np.asarray(prices, dtype="float64"), space)
    method = cfg.cluster_method.lower()

    if method == "grade":
        if space != "linear" or grid_step <= 0:
            raise ValueError("--metodo grade so existe no modo renko")
        labels, peaks = _cluster_grade(x, grid_step, cfg.min_events)
        info = {"method": "grade", "band": grid_step, "peaks": peaks}
    elif method == "kde":
        peaks, grid, dens = kde.density_peaks(
            x, weights, bandwidth=band, grid_n=cfg.kde_grid,
            prominence_frac=cfg.kde_prominence, min_distance=min_distance,
        )
        labels = kde.assign(x, peaks, radius=cfg.kde_assign_factor * band)
        peak_prices = peaks if space == "linear" else np.exp(peaks)
        grid_prices = grid if space == "linear" else np.exp(grid)
        info = {"method": "kde", "band": band, "peaks": peak_prices,
                "grid": grid_prices, "density": dens}
    elif method == "dbscan":
        labels = dbscan.cluster_1d(x, eps=band, min_samples=cfg.min_events)
        info = {"method": "dbscan", "eps": band}
    elif method == "hierarchical":
        labels = hierarchical.cluster_1d(x, eps=band, min_samples=cfg.min_events)
        info = {"method": "hierarchical", "eps": band}
    else:
        raise ValueError(f"cluster_method invalido: {cfg.cluster_method}")

    assigned = labels[labels >= 0]
    info["space"] = space
    info["n_clusters"] = int(len(set(assigned)))
    info["n_ruido"] = int((labels < 0).sum())
    # fracao dos eventos no maior cluster: denuncia encadeamento (tipico do
    # DBSCAN em 1-D), quando um unico cluster engole toda a faixa de precos
    info["maior_cluster"] = (
        float(np.bincount(assigned).max() / assigned.size) if assigned.size else 0.0
    )
    return labels, info
