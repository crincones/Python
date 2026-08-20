"""Validacao estatistica dos niveis (secao 27).

Os niveis avaliados aqui devem ter sido construidos SOMENTE com dados
anteriores a janela de teste (secao 28). Este modulo apenas mede o que
aconteceu depois.

Metricas por nivel, medidas fora da amostra:
  * quantas vezes o preco voltou ao nivel (retornos independentes);
  * reacao media / mediana / maxima depois do retorno;
  * a mesma reacao normalizada pela volatilidade vigente;
  * minutos ate o proximo movimento significativo depois do toque.

Para saber se o numero significa algo, o resultado e comparado a um grupo de
controle de precos que o mercado negociou mas que o algoritmo nao apontou.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from data.resampling import atr_reference, resample_ohlcv
from detection.reactions import forward_extremes


def _independent_touches(
    high: np.ndarray,
    low: np.ndarray,
    price: float,
    tol: float,
    departure: float,
) -> np.ndarray:
    """Posicoes dos retornos independentes ao nivel.

    Um novo retorno so conta depois que o preco se afastou mais de `departure`
    do nivel -- mesmo criterio de independencia usado na deteccao (secao 8).
    """
    touch = (low <= price + tol) & (high >= price - tol)
    idx = np.flatnonzero(touch)
    if idx.size == 0:
        return idx

    keep = [idx[0]]
    excursion = 0.0
    for k in range(1, idx.size):
        a, b = idx[k - 1] + 1, idx[k]
        if b > a:
            excursion = max(high[a:b].max() - price, price - low[a:b].min())
        else:
            excursion = 0.0
        if excursion > departure:
            keep.append(idx[k])
    return np.array(keep, dtype="int64")


def _bars_to_move(
    high: np.ndarray,
    low: np.ndarray,
    pos: np.ndarray,
    price: float,
    threshold: float,
    max_bars: int,
) -> float:
    """Minutos medios ate o proximo movimento significativo depois do toque.

    'Significativo' = afastar-se mais de `threshold` (1 ATR) do nivel. Toques
    que nao produzem esse movimento dentro de `max_bars` sao contados como
    `max_bars` (censura a direita), o que penaliza niveis inertes.
    """
    n = high.size
    out = np.empty(pos.size, dtype="float64")
    for k, i in enumerate(pos):
        a, b = i + 1, min(i + 1 + max_bars, n)
        if b <= a:
            out[k] = max_bars
            continue
        exc = np.maximum(high[a:b] - price, price - low[a:b])
        hit = np.flatnonzero(exc > threshold)
        out[k] = float(hit[0] + 1) if hit.size else float(max_bars)
    return float(out.mean()) if out.size else np.nan


def evaluate_prices(
    df: pd.DataFrame,
    prices,
    cfg,
    horizon: int = 60,
    touch_tol_atr: float = 0.10,
    departure_atr: float = 0.75,
) -> pd.DataFrame:
    """Mede o comportamento posterior de uma lista de precos em `df`."""
    cols = ["price", "n_touches", "mean_reaction", "median_reaction", "max_reaction",
            "mean_strength", "median_strength", "mean_bars_to_move"]
    if df.empty or len(prices) == 0:
        return pd.DataFrame(columns=cols)

    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    ref_bars = resample_ohlcv(df, cfg.atr_ref_tf)
    atr_ref = atr_reference(df, ref_bars, cfg.atr_period)
    fmax, fmin = forward_extremes(high, low, horizon)

    from config import TF_MINUTES
    ref_minutes = TF_MINUTES.get(cfg.atr_ref_tf, 60)
    expected = atr_ref * np.sqrt(horizon / max(ref_minutes, 1.0))

    lo_visited, hi_visited = float(low.min()), float(high.max())
    rows = []
    for p in prices:
        p = float(p)
        if not (lo_visited <= p <= hi_visited):
            rows.append({"price": p, "n_touches": 0, "mean_reaction": np.nan,
                         "median_reaction": np.nan, "max_reaction": np.nan,
                         "mean_strength": np.nan, "median_strength": np.nan,
                         "mean_bars_to_move": np.nan})
            continue

        med_atr = float(np.median(atr_ref))
        pos = _independent_touches(high, low, p, touch_tol_atr * med_atr,
                                   departure_atr * med_atr)
        if pos.size == 0:
            rows.append({"price": p, "n_touches": 0, "mean_reaction": np.nan,
                         "median_reaction": np.nan, "max_reaction": np.nan,
                         "mean_strength": np.nan, "median_strength": np.nan,
                         "mean_bars_to_move": np.nan})
            continue

        react = np.fmax(fmax[pos] - p, p - fmin[pos])
        ok = np.isfinite(react)
        react = np.maximum(react[ok], 0.0)
        strength = react / expected[pos][ok]

        rows.append({
            "price": p,
            "n_touches": int(pos.size),
            "mean_reaction": float(np.mean(react)) if react.size else np.nan,
            "median_reaction": float(np.median(react)) if react.size else np.nan,
            "max_reaction": float(np.max(react)) if react.size else np.nan,
            "mean_strength": float(np.mean(strength)) if react.size else np.nan,
            "median_strength": float(np.median(strength)) if react.size else np.nan,
            "mean_bars_to_move": _bars_to_move(high, low, pos, p, med_atr, 4 * horizon),
        })

    return pd.DataFrame(rows)


def baseline_prices(
    source: pd.DataFrame,
    target: pd.DataFrame,
    n: int,
    tick: float,
    seed: int = 7,
) -> np.ndarray:
    """Grupo de controle: precos que o mercado realmente negociou, mas que o
    algoritmo NAO apontou como importantes.

    Sortear uniformemente dentro da faixa seria um controle fraco: precos pouco
    visitados quase nunca sao tocados e, quando sao, e no extremo de um
    movimento -- o que inflaria artificialmente a reacao do controle. Por isso
    os precos de controle sao sorteados entre os fechamentos observados em
    `source` (o periodo de treino) restritos a faixa percorrida em `target`.
    """
    rng = np.random.default_rng(seed)
    lo, hi = float(target["low"].min()), float(target["high"].max())
    pool = source["close"].to_numpy()
    pool = pool[(pool >= lo) & (pool <= hi)]
    if pool.size == 0:
        pool = np.array([lo, hi])
    raw = rng.choice(pool, size=n, replace=True)
    return np.unique(np.round(raw / tick) * tick)


def compare(levels_eval: pd.DataFrame, base_eval: pd.DataFrame) -> Dict:
    """Resumo comparativo entre niveis detectados e precos aleatorios."""
    def agg(d):
        touched = d[d["n_touches"] > 0]
        return {
            "n": int(len(d)),
            "pct_tocados": round(100.0 * len(touched) / max(len(d), 1), 1),
            "toques_medios": round(float(d["n_touches"].mean()), 2),
            "reacao_media": round(float(touched["mean_reaction"].mean()), 1) if len(touched) else np.nan,
            "forca_media": round(float(touched["mean_strength"].mean()), 3) if len(touched) else np.nan,
            "forca_mediana": round(float(touched["median_strength"].median()), 3) if len(touched) else np.nan,
            "min_ate_movimento": round(float(touched["mean_bars_to_move"].mean()), 1) if len(touched) else np.nan,
        }

    a, b = agg(levels_eval), agg(base_eval)
    ratio = (a["forca_media"] / b["forca_media"]) if (b["forca_media"] and np.isfinite(b["forca_media"])) else np.nan
    ratio_t = (a["toques_medios"] / b["toques_medios"]) if b["toques_medios"] else np.nan
    return {
        "niveis": a,
        "aleatorio": b,
        "razao_forca": round(float(ratio), 3) if np.isfinite(ratio) else np.nan,
        "razao_toques": round(float(ratio_t), 3) if np.isfinite(ratio_t) else np.nan,
    }
