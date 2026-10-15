"""Gráfico de payoff no vencimento em PNG (matplotlib), no mesmo desenho do relatório HTML."""

from __future__ import annotations

import io
from collections.abc import Mapping
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from screener.notify.format import brl, num  # noqa: E402
from screener.spreads.builder import BULL_CALL  # noqa: E402

# Mesmos tokens do tema claro do relatório (report/templates/relatorio.html.j2).
GAIN = "#2a78d6"
LOSS = "#e34948"
WASH_ALPHA = 0.18
INK = "#1f1f1e"
SECONDARY = "#5f5e5a"
MUTED = "#8a8984"
GRID = "#e6e5e0"
STEPS = 240
MIN_PAD_PCT_SPOT = 0.04
HEADROOM = 0.18
FIGSIZE = (8.0, 4.5)
DPI = 150


def payoff_per_lot(spread: Mapping[str, Any], prices: np.ndarray, lot_size: int) -> np.ndarray:
    """Resultado da trava no vencimento, por lote, para cada preço do ativo."""
    if spread["strategy"] == BULL_CALL:
        intrinsic = prices - spread["long_strike"]
    else:
        intrinsic = spread["long_strike"] - prices
    return (np.clip(intrinsic, 0, spread["width"]) - spread["debit"]) * lot_size


def payoff_png(spread: Mapping[str, Any], lot_size: int, title: str) -> bytes:
    """PNG do payoff: ganho em azul, perda em vermelho, spot tracejado e breakeven pontilhado."""
    low = min(spread["long_strike"], spread["short_strike"])
    high = max(spread["long_strike"], spread["short_strike"])
    spot, breakeven = spread["spot"], spread["breakeven"]
    ref = [low, high, spot, breakeven]
    pad = max(high - low, spot * MIN_PAD_PCT_SPOT)
    prices = np.sort(
        np.concatenate(
            [np.linspace(min(ref) - pad, max(ref) + pad, STEPS + 1), [low, high, breakeven]]
        )
    )
    result = payoff_per_lot(spread, prices, lot_size)
    gain, loss = spread["max_gain_per_lot"], -spread["max_loss_per_lot"]

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    try:
        ax.fill_between(prices, np.maximum(result, 0), 0, color=GAIN, alpha=WASH_ALPHA, lw=0)
        ax.fill_between(prices, np.minimum(result, 0), 0, color=LOSS, alpha=WASH_ALPHA, lw=0)
        ax.plot(prices, result, color=INK, lw=2)
        ax.axhline(0, color=MUTED, lw=1)
        ax.axvline(spot, color=MUTED, lw=1.5, ls="--")
        ax.axvline(breakeven, color=SECONDARY, lw=1.5, ls=":")

        headroom = (gain - loss) * HEADROOM
        ax.set_ylim(loss - headroom, gain + headroom)
        ax.set_xlim(prices[0], prices[-1])
        label = {"fontsize": 9, "color": SECONDARY, "ha": "center"}
        box = {"facecolor": "white", "edgecolor": "none", "pad": 1.5}
        top = gain + headroom * 0.55
        ax.text(spot, top, f"Spot {num(spot)}", bbox=box, **label)
        ax.text(breakeven, top - headroom * 0.45, f"Breakeven {num(breakeven)}", bbox=box, **label)

        gain_right = spread["strategy"] == BULL_CALL
        x_gain, x_loss = (0.99, 0.01) if gain_right else (0.01, 0.99)
        side = {"fontsize": 9, "color": SECONDARY, "transform": ax.get_yaxis_transform()}
        ax.text(x_gain, gain, f"ganho máx. {brl(gain)}", ha="right" if gain_right else "left",
                va="bottom", **side)  # fmt: skip
        ax.text(x_loss, loss, f"perda máx. {brl(loss)}", ha="left" if gain_right else "right",
                va="top", **side)  # fmt: skip

        ax.set_title(title, fontsize=11, color=INK, loc="left")
        ax.set_xlabel("Preço do ativo no vencimento (R$)", color=MUTED)
        ax.set_ylabel("R$ por lote", color=MUTED)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0)))
        ax.grid(color=GRID, lw=0.8)
        ax.tick_params(colors=SECONDARY, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", facecolor="white")
    finally:
        plt.close(fig)
    return buffer.getvalue()
