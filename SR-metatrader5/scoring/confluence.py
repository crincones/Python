"""Confluencia (secao 22).

Confluencia NAO cria linhas novas: e uma propriedade do nivel. Se varias fontes
independentes (swings de escalas diferentes, maxima semanal, fechamento mensal)
apontam para o mesmo preco, o nivel continua sendo um so -- o score sobe.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def confluence_stats(sub: pd.DataFrame, scale_weights: dict) -> dict:
    """Diversidade de fontes que sustentam um nivel."""
    pairs = set(zip(sub["scale"], sub["source"]))
    tfs = sub["scale"].unique()
    srcs = sub["source"].unique()

    weight = float(np.sum([scale_weights.get(tf, 1.0) for tf in tfs]))
    return {
        "n_scales": int(len(tfs)),
        "n_sources": int(len(srcs)),
        "n_pairs": int(len(pairs)),
        "scale_weight": weight,
    }
