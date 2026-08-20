"""Grafico de inspecao: candles + linhas horizontais (secao 30).

Sao LINHAS, nunca retangulos ou zonas. Espessura e transparencia refletem o
score -- isso e apenas visualizacao, nao faz parte da definicao do nivel.
"""

from __future__ import annotations

import os
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection

from data.resampling import resample_ohlcv
from models.level import Level


def _draw_candles(ax, bars: pd.DataFrame):
    x = np.arange(len(bars))
    o = bars["open"].to_numpy()
    h = bars["high"].to_numpy()
    l = bars["low"].to_numpy()
    c = bars["close"].to_numpy()
    up = c >= o

    wicks = [[(xi, li), (xi, hi)] for xi, li, hi in zip(x, l, h)]
    ax.add_collection(LineCollection(wicks, colors="#8a8a8a", linewidths=0.4, zorder=1))

    bodies = [[(xi, oi), (xi, ci)] for xi, oi, ci in zip(x, o, c)]
    colors = np.where(up, "#2e7d32", "#c62828")
    ax.add_collection(LineCollection(bodies, colors=colors, linewidths=1.6, zorder=2))

    ax.set_xlim(-1, len(bars))

    step = max(len(bars) // 12, 1)
    ticks = x[::step]
    ax.set_xticks(ticks)
    ax.set_xticklabels([bars.index[i].strftime("%d/%m/%y") for i in ticks], fontsize=8)

    return float(l.min()), float(h.max())


def _draw_renko(ax, bricks: pd.DataFrame):
    """Tijolos do Renko: corpo cheio e pavio fino, como no ProfitChart."""
    x = np.arange(len(bricks))
    o = bricks["open"].to_numpy()
    c = bricks["close"].to_numpy()
    h = bricks["high"].to_numpy()
    l = bricks["low"].to_numpy()
    up = c > o

    wicks = [[(xi, li), (xi, hi)] for xi, li, hi in zip(x, l, h)]
    ax.add_collection(LineCollection(wicks, colors="#b0b0b0", linewidths=0.3, zorder=1))

    bodies = [[(xi, oi), (xi, ci)] for xi, oi, ci in zip(x, o, c)]
    colors = np.where(up, "#2e7d32", "#c62828")
    lw = max(min(900.0 / max(len(bricks), 1), 3.0), 0.5)
    ax.add_collection(LineCollection(bodies, colors=colors, linewidths=lw, zorder=2))

    ax.set_xlim(-1, len(bricks))
    step = max(len(bricks) // 12, 1)
    ticks = x[::step]
    ax.set_xticks(ticks)
    ax.set_xticklabels([bricks["timestamp"].iloc[i].strftime("%d/%m/%y") for i in ticks],
                       fontsize=8)
    return float(l.min()), float(h.max())


def plot_levels(
    df: pd.DataFrame,
    levels: List[Level],
    out_path: str,
    chart_tf: str = "1D",
    title: str = "Niveis importantes",
    density: Optional[tuple] = None,
    last_days: int = 0,
    bricks: Optional[pd.DataFrame] = None,
    digits: int = 0,
):
    """Desenha o grafico analisado (Renko, se houver) com as linhas por cima."""
    if last_days and len(df):
        cut = df.index[-1] - pd.Timedelta(days=last_days)
        df = df.loc[df.index >= cut]
        if bricks is not None:
            bricks = bricks.loc[bricks["timestamp"] >= cut]

    if bricks is not None and len(bricks):
        bars = bricks
    else:
        bars = resample_ohlcv(df, chart_tf) if chart_tf not in ("1min", None) else df
    if bars.empty:
        return None

    has_dens = density is not None
    fig, axes = plt.subplots(
        1, 2 if has_dens else 1,
        figsize=(17, 9),
        sharey=True,
        gridspec_kw={"width_ratios": [4, 1]} if has_dens else None,
    )
    ax = axes[0] if has_dens else axes

    lo_px, hi_px = (_draw_renko(ax, bars) if bricks is not None and len(bricks)
                    else _draw_candles(ax, bars))

    # O eixo de precos foca no que importa: as linhas desenhadas e o trecho
    # recente do grafico. Sem isso, um historico que percorreu 70.000 pontos
    # espreme as linhas -- e os rotulos -- em uma faixa ilegivel.
    if levels:
        recent = bars.iloc[int(len(bars) * 0.75):]
        lo_px = min(min(lv.price for lv in levels), float(recent["low"].min()))
        hi_px = max(max(lv.price for lv in levels), float(recent["high"].max()))
    pad = (hi_px - lo_px) * 0.06
    ax.set_ylim(lo_px - pad, hi_px + pad)

    if levels:
        smin = min(lv.score for lv in levels)
        smax = max(lv.score for lv in levels)
        rng = max(smax - smin, 1e-9)
        for lv in levels:
            t = (lv.score - smin) / rng
            ax.axhline(lv.price, color="#1565c0", linestyle="--",
                       linewidth=0.8 + 1.6 * t, alpha=0.35 + 0.6 * t, zorder=3)
            ax.text(len(bars) * 0.998, lv.price,
                    f" {lv.price:,.{digits}f}  R{lv.score:.0f} T{lv.n_events}",
                    va="center", ha="left", fontsize=7.5, color="#0d47a1")

    ax.set_title(title, fontsize=12)
    ax.grid(alpha=0.15)
    ax.margins(x=0.02)

    if has_dens:
        grid_price, dens = density
        axd = axes[1]
        axd.plot(dens, grid_price, color="#1565c0", linewidth=1.0)
        axd.fill_betweenx(grid_price, 0, dens, color="#1565c0", alpha=0.15)
        for lv in levels:
            axd.axhline(lv.price, color="#1565c0", linewidth=0.4, alpha=0.4)
        axd.set_title("densidade de eventos", fontsize=9)
        axd.set_xticks([])
        axd.grid(alpha=0.15)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path
