"""
Construcao do grafico Renko a partir dos candles de 1 minuto.

A especificacao foi conferida contra um export 50R do proprio ProfitChart
(`historico 50R.csv`):

  * a caixa de "50R" no WIN mede 245 pontos, ou seja (50 - 1) ticks de 5 pts;
  * a grade e ancorada em ZERO -- todas as aberturas e fechamentos de tijolo
    sao multiplos exatos da caixa (171.500 = 245 x 700);
  * continuacao anda 1 caixa; reversao exige 2 caixas (a abertura do tijolo
    volta para a abertura do anterior);
  * cada tijolo carrega a maxima e a minima REAIS do periodo que ele cobre
    (pavios de ate 2 caixas alem do corpo).

Como o candle de 1 minuto nao informa o caminho percorrido dentro da barra,
usa-se a convencao usual: em minuto de alta processa-se a minima antes da
maxima; em minuto de baixa, o contrario.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

BRICK_COLUMNS = ["timestamp", "pos", "direction", "open", "close", "high", "low", "volume"]


def box_from_ticks(ticks: int, tick_size: float) -> float:
    """Converte "NR" do ProfitChart em pontos: (N - 1) ticks."""
    return float((ticks - 1) * tick_size)


def build_renko(
    df: pd.DataFrame,
    box: float,
    anchor: float = 0.0,
) -> pd.DataFrame:
    """Devolve os tijolos Renko gerados pelo historico de 1 minuto.

    Colunas: timestamp e pos (minuto em que o tijolo fechou), direction (+1/-1),
    open, close (na grade), high, low (extremos reais do trecho coberto) e
    volume acumulado.
    """
    if box <= 0:
        raise ValueError("box deve ser positivo")

    o_ = df["open"].to_numpy()
    h_ = df["high"].to_numpy()
    l_ = df["low"].to_numpy()
    c_ = df["close"].to_numpy()
    v_ = df["volume"].to_numpy()
    n = len(df)

    # primeiro fechamento na grade (a grade do ProfitChart e ancorada em zero)
    base = np.floor((o_[0] - anchor) / box) * box + anchor
    last_open = base
    last_close = base
    direction = 0

    out_pos, out_dir, out_open, out_close = [], [], [], []
    out_high, out_low, out_vol = [], [], []

    run_hi = -np.inf
    run_lo = np.inf
    run_vol = 0.0

    for i in range(n):
        hi, lo = h_[i], l_[i]
        run_hi = hi if hi > run_hi else run_hi
        run_lo = lo if lo < run_lo else run_lo
        vol = v_[i]
        run_vol += 0.0 if vol != vol else vol  # NaN-safe

        # ordem de percurso dentro do minuto
        path = (lo, hi) if c_[i] >= o_[i] else (hi, lo)

        for px in path:
            while True:
                if direction >= 0 and px >= last_close + box:
                    new_open, new_close, d = last_close, last_close + box, 1
                elif direction <= 0 and px <= last_close - box:
                    new_open, new_close, d = last_close, last_close - box, -1
                elif direction > 0 and px <= last_open - box:
                    # reversao para baixo: 2 caixas medidas do fechamento
                    new_open, new_close, d = last_open, last_open - box, -1
                elif direction < 0 and px >= last_open + box:
                    new_open, new_close, d = last_open, last_open + box, 1
                else:
                    break

                out_pos.append(i)
                out_dir.append(d)
                out_open.append(new_open)
                out_close.append(new_close)
                out_high.append(run_hi)
                out_low.append(run_lo)
                out_vol.append(run_vol)

                last_open, last_close, direction = new_open, new_close, d
                run_hi, run_lo, run_vol = hi, lo, 0.0

    if not out_pos:
        return pd.DataFrame(columns=BRICK_COLUMNS)

    pos = np.array(out_pos, dtype="int64")
    bricks = pd.DataFrame({
        "timestamp": df.index[pos],
        "pos": pos,
        "direction": np.array(out_dir, dtype="int8"),
        "open": np.array(out_open),
        "close": np.array(out_close),
        "high": np.array(out_high),
        "low": np.array(out_low),
        "volume": np.array(out_vol),
    })
    # o pavio nunca pode ficar dentro do corpo
    bricks["high"] = np.maximum(bricks["high"], bricks[["open", "close"]].max(axis=1))
    bricks["low"] = np.minimum(bricks["low"], bricks[["open", "close"]].min(axis=1))
    return bricks
