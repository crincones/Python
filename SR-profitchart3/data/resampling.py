"""Derivacao das escalas maiores a partir dos candles de 1 minuto (secao 13)."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Reamostra o historico de 1m para `rule`.

    Alem do OHLCV, devolve para cada barra:
      * `hi_pos` / `lo_pos`: posicao (na serie de 1m) do minuto em que a maxima
        e a minima ocorreram -- necessario para medir a reacao a partir do
        instante exato da interacao, sem esperar o fechamento da barra;
      * `first_pos` / `last_pos`: primeiro e ultimo minuto da barra.
    """
    if rule in ("1min", "1T"):
        bars = df.copy()
        pos = np.arange(len(df))
        bars["hi_pos"] = pos
        bars["lo_pos"] = pos
        bars["first_pos"] = pos
        bars["last_pos"] = pos
        return bars

    g = df.groupby(pd.Grouper(freq=rule, label="left", closed="left"), sort=True)
    bars = g.agg(AGG)
    bars = bars.dropna(subset=["open"])
    if bars.empty:
        return bars

    # Bin de cada minuto -> indice da barra ja observada (evita grupos vazios).
    edges = bars.index.to_numpy()
    bin_id = np.searchsorted(edges, df.index.to_numpy(), side="right") - 1
    valid = bin_id >= 0

    # Series indexadas pela posicao absoluta em `df`: idxmax/idxmin devolvem
    # diretamente a posicao do minuto extremo.
    pos = np.arange(len(df))[valid]
    bid = bin_id[valid]
    hi = pd.Series(df["high"].to_numpy()[valid], index=pos).groupby(bid).idxmax()
    lo = pd.Series(df["low"].to_numpy()[valid], index=pos).groupby(bid).idxmin()
    first = pd.Series(pos, index=pos).groupby(bid).min()
    last = pd.Series(pos, index=pos).groupby(bid).max()

    idx = np.arange(len(bars))
    for name, s in (("hi_pos", hi), ("lo_pos", lo), ("first_pos", first), ("last_pos", last)):
        bars[name] = s.reindex(idx).to_numpy().astype("int64")
    return bars


def atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR de Wilder sobre uma serie OHLC qualquer."""
    h = bars["high"].to_numpy()
    l = bars["low"].to_numpy()
    pc = np.concatenate([[np.nan], bars["close"].to_numpy()[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    s = pd.Series(tr, index=bars.index)
    return s.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def build_timeframes(df: pd.DataFrame, rules) -> Dict[str, pd.DataFrame]:
    return {r: resample_ohlcv(df, r) for r in rules}


def atr_reference(df: pd.DataFrame, bars: pd.DataFrame, period: int) -> np.ndarray:
    """ATR de referencia projetado sobre cada minuto, sem look-ahead.

    O valor usado em um minuto e o ATR da ultima barra JA FECHADA da escala de
    referencia (shift de 1 barra).
    """
    a = atr(bars, period).shift(1)
    ref = a.reindex(df.index, method="ffill").to_numpy()
    med = np.nanmedian(ref)
    if not np.isfinite(med):
        med = float(np.nanmedian(df["high"].to_numpy() - df["low"].to_numpy())) * 10.0
    return np.where(np.isfinite(ref) & (ref > 0), ref, med)


def relative_volume(df: pd.DataFrame, window: int) -> np.ndarray:
    """Volume do minuto dividido pela media movel longa (secao 21).

    Devolve NaN quando o ativo nao possui volume.
    """
    v = df["volume"].to_numpy(dtype="float64")
    if not np.isfinite(v).any() or np.nansum(v) <= 0:
        return np.full(len(df), np.nan)
    s = pd.Series(v)
    base = s.rolling(window, min_periods=max(50, window // 20)).mean()
    base = base.bfill()
    out = (s / base).to_numpy()
    return np.where(np.isfinite(out), out, np.nan)
