"""
Eventos extraidos de UM unico grafico: o Renko.

No Renko nao existe "tempo grafico": a estrutura vem do proprio encadeamento
dos tijolos. O que substitui a hierarquia de escalas e a PROFUNDIDADE do pivo
-- quantos tijolos o mercado andou para chegar ao ponto e quantos andou para
sair dele. Um giro de 2 tijolos e ruido; um giro de 10 tijolos e estrutura.

  profundidade = min(tijolos antes do giro, tijolos depois do giro)

Toda a medicao (reacao, tolerancia, independencia) e feita em CAIXAS, nao em
pontos nem em ATR: a caixa ja e a unidade natural de volatilidade do grafico.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from detection.reactions import forward_extremes
from models.level import EVENT_COLUMNS

# faixas de profundidade -> rotulo usado como "escala" do evento
DEPTH_BINS = [(1, "d1"), (2, "d2"), (4, "d3"), (7, "d5"), (10 ** 9, "d8")]


def depth_label(depth: np.ndarray) -> np.ndarray:
    out = np.empty(depth.shape, dtype=object)
    prev = 0
    for limit, name in DEPTH_BINS:
        out[(depth > prev) & (depth <= limit)] = name
        prev = limit
    return out


def find_pivots(bricks: pd.DataFrame) -> pd.DataFrame:
    """Pontos de giro do Renko, com a profundidade de cada um.

    O extremo de uma sequencia de tijolos e o fechamento do ultimo tijolo dela:
    e exatamente a linha da grade que o grafico mostra como topo ou fundo.
    """
    d = bricks["direction"].to_numpy()
    n = d.size
    if n < 3:
        return pd.DataFrame(columns=["brick", "depth", "grid_price", "extreme_price"])

    change = np.flatnonzero(np.diff(d) != 0)
    if change.size < 2:
        return pd.DataFrame(columns=["brick", "depth", "grid_price", "extreme_price"])

    run_end = np.concatenate([change, [n - 1]])
    run_start = np.concatenate([[0], change + 1])
    run_len = run_end - run_start + 1

    # cada giro fica no fim de uma sequencia (a ultima ainda esta em formacao)
    idx = np.arange(run_end.size - 1)
    brick = run_end[idx]
    depth = np.minimum(run_len[idx], run_len[idx + 1])

    close = bricks["close"].to_numpy()
    high = bricks["high"].to_numpy()
    low = bricks["low"].to_numpy()
    up = d[brick] > 0

    return pd.DataFrame({
        "brick": brick,
        "depth": depth,
        "grid_price": close[brick],
        # preco real onde o mercado virou (ponta do pavio do tijolo do giro)
        "extreme_price": np.where(up, high[brick], low[brick]),
    })


def _group_independent(
    brick: np.ndarray,
    price: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    tol: float,
    departure: float,
) -> np.ndarray:
    """Giros no mesmo preco so contam de novo apos o mercado se afastar."""
    n = brick.size
    labels = np.empty(n, dtype="int64")
    if n == 0:
        return labels

    label = 0
    labels[0] = 0
    ref_price = price[0]
    ref_brick = brick[0]

    for i in range(1, n):
        same = abs(price[i] - ref_price) <= tol
        if same:
            a, b = ref_brick + 1, brick[i]
            if b > a:
                excursion = max(high[a:b].max() - ref_price, ref_price - low[a:b].min())
            else:
                excursion = 0.0
            if excursion <= departure:
                ref_brick = brick[i]
                labels[i] = label
                continue
        label += 1
        ref_price = price[i]
        ref_brick = brick[i]
        labels[i] = label

    return labels


def build_renko_events(
    bricks: pd.DataFrame,
    df: pd.DataFrame,
    cfg,
    rel_vol: np.ndarray,
    box: float,
) -> pd.DataFrame:
    """Eventos candidatos do grafico Renko, ja com reacao medida em caixas."""
    piv = find_pivots(bricks)
    if piv.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS + ["n_bars", "depth"])

    method = cfg.renko_price_method
    if method == "renko":
        price = piv["grid_price"].to_numpy()
    elif method == "extreme":
        price = piv["extreme_price"].to_numpy()
    elif method == "close":
        price = df["close"].to_numpy()[bricks["pos"].to_numpy()[piv["brick"].to_numpy()]]
    else:
        raise ValueError(f"renko_price_method invalido: {method}")

    high = bricks["high"].to_numpy()
    low = bricks["low"].to_numpy()

    labels = _group_independent(
        piv["brick"].to_numpy(), price, high, low,
        tol=cfg.renko_merge_boxes * box,
        departure=cfg.renko_departure_boxes * box,
    )

    ev = pd.DataFrame({"brick": piv["brick"].to_numpy(), "price": price,
                       "depth": piv["depth"].to_numpy(), "_g": labels})
    agg = ev.groupby("_g", sort=True).agg(
        brick=("brick", "max"),
        price=("price", "median"),
        depth=("depth", "max"),
        n_bars=("brick", "size"),
    ).reset_index(drop=True)

    # ---------------------------------------------------------- reacao
    # A reacao bruta cresce com o horizonte, entao horizontes diferentes so sao
    # comparaveis depois de divididos pelo deslocamento tipico de uma caminhada
    # aleatoria de `h` tijolos, que e `caixa * sqrt(h)`. A forca do giro e o
    # maior desses valores: ~1 = tao longe quanto o acaso levaria.
    b = agg["brick"].to_numpy()
    p = agg["price"].to_numpy()
    best_strength = np.zeros(p.size)
    best_reaction = np.zeros(p.size)
    for h in cfg.renko_horizons:
        fmax, fmin = forward_extremes(high, low, h)
        react = np.fmax(fmax[b] - p, p - fmin[b])
        react = np.where(np.isfinite(react), np.maximum(react, 0.0), 0.0)
        strength = react / (box * np.sqrt(h))
        upd = strength > best_strength
        best_strength = np.where(upd, strength, best_strength)
        best_reaction = np.where(upd, react, best_reaction)

    pos = bricks["pos"].to_numpy()[b]
    out = pd.DataFrame({
        "timestamp": df.index[pos],
        "pos": pos,
        "price": p,
        "scale": depth_label(agg["depth"].to_numpy()),
        "source": "renko_pivot",
        "reaction": best_reaction,
        "strength": best_strength,
        "rel_volume": rel_vol[pos],
        "atr": box,
        "n_bars": agg["n_bars"].to_numpy(),
        "depth": agg["depth"].to_numpy(),
    })

    out = out[out["strength"] >= cfg.renko_min_strength]
    out = out.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    return out[EVENT_COLUMNS + ["n_bars", "depth"]]
