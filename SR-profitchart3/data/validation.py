"""Normalizacao: candles invalidos, gaps e tick size (secao 5 do descritivo)."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

_SCALE = 100_000  # preserva ate 5 casas decimais ao trabalhar em inteiros


def infer_tick_size(prices: np.ndarray) -> float:
    """Infere o tick size do ativo a partir dos precos observados.

    Estrategia: MDC das diferencas entre precos distintos (em unidades inteiras
    escaladas). Se o MDC degenerar, cai para a diferenca positiva mais frequente.
    """
    p = np.asarray(prices, dtype="float64")
    p = p[np.isfinite(p)]
    if p.size == 0:
        return 1.0

    ip = np.unique(np.rint(p * _SCALE).astype("int64"))
    if ip.size < 2:
        return 1.0

    d = np.diff(ip)
    d = d[d > 0]
    g = int(np.gcd.reduce(d))
    tick = g / _SCALE

    if tick <= 0:
        vals, counts = np.unique(d, return_counts=True)
        tick = float(vals[np.argmax(counts)]) / _SCALE
    return float(tick)


def normalize_to_tick(price, tick_size: float):
    """round(price / tick) * tick -- nunca round(price, 2)."""
    if tick_size is None or tick_size <= 0:
        return price
    return np.round(np.asarray(price, dtype="float64") / tick_size) * tick_size


def validate_candles(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Remove candles invalidos e devolve um relatorio de qualidade dos dados."""
    n0 = len(df)
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))

    finite = np.isfinite(o) & np.isfinite(h) & np.isfinite(l) & np.isfinite(c)
    positive = (o > 0) & (h > 0) & (l > 0) & (c > 0)
    coherent = (h >= l) & (h >= np.maximum(o, c)) & (l <= np.minimum(o, c))
    ok = finite & positive & coherent

    clean = df.loc[ok].copy()

    delta = clean.index.to_series().diff().dt.total_seconds().div(60.0)
    one_min = float((delta == 1).sum())
    gaps = delta[delta > 1]

    report = {
        "linhas_lidas": n0,
        "linhas_validas": int(len(clean)),
        "descartadas_invalidas": int(n0 - len(clean)),
        "inicio": clean.index[0] if len(clean) else None,
        "fim": clean.index[-1] if len(clean) else None,
        "pct_continuidade_1m": round(100.0 * one_min / max(len(clean) - 1, 1), 2),
        "gaps": int(len(gaps)),
        "gap_maior_min": float(gaps.max()) if len(gaps) else 0.0,
        "volume_disponivel": bool(np.isfinite(clean["volume"].to_numpy()).any()
                                  and float(np.nansum(clean["volume"].to_numpy())) > 0),
    }
    return clean, report


def prepare(df: pd.DataFrame, tick_size: Optional[float] = None) -> Tuple[pd.DataFrame, float, Dict]:
    """Valida, infere o tick e normaliza os precos a grade do ativo."""
    clean, report = validate_candles(df)
    tick = tick_size if tick_size else infer_tick_size(clean[["open", "high", "low", "close"]].to_numpy().ravel())
    for c in ("open", "high", "low", "close"):
        clean[c] = normalize_to_tick(clean[c].to_numpy(), tick)
    report["tick_size"] = tick
    return clean, tick, report
