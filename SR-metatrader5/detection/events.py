"""Construcao dos eventos candidatos (secoes 7, 8 e 9).

Um evento e uma REGIAO TEMPORAL de interacao com um preco -- nunca um candle
isolado. Interacoes consecutivas com o mesmo preco so viram eventos distintos
depois que o mercado se afasta o suficiente (secao 8).
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from data.resampling import resample_ohlcv
from detection.reactions import build_excursion_tables, measure
from detection.reference_levels import reference_events
from detection.swings import find_swings
from models.level import EVENT_COLUMNS

PRICE_METHODS = ("extreme", "close", "mid", "reaction_price")


def _group_independent(
    pos: np.ndarray,
    price: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr_ref: np.ndarray,
    factor: float,
) -> np.ndarray:
    """Rotula interacoes consecutivas que pertencem ao mesmo evento.

    Duas interacoes proximas so sao independentes quando, entre elas, o preco
    se afastou mais de `factor * ATR` do nivel.
    """
    n = pos.size
    labels = np.empty(n, dtype="int64")
    if n == 0:
        return labels

    label = 0
    labels[0] = 0
    ref_price = price[0]
    ref_pos = pos[0]

    for i in range(1, n):
        thr = factor * atr_ref[pos[i]]
        same_price = abs(price[i] - ref_price) <= thr

        departed = True
        if same_price:
            a, b = ref_pos + 1, pos[i]
            if b > a:
                seg_hi = high[a:b].max()
                seg_lo = low[a:b].min()
                excursion = max(seg_hi - ref_price, ref_price - seg_lo)
            else:
                excursion = 0.0
            departed = excursion > thr

        if same_price and not departed:
            # mesma interacao: o evento se estende ate aqui
            ref_pos = pos[i]
        else:
            label += 1
            ref_price = price[i]
            ref_pos = pos[i]
        labels[i] = label

    return labels


def _collapse(df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Colapsa interacoes rotuladas em um unico evento por rotulo."""
    df = df.assign(_g=labels)
    agg = df.groupby("_g", sort=True).agg(
        pos=("pos", "max"),
        price=("price", "median"),
        n_bars=("pos", "size"),
    )
    return agg.reset_index(drop=True)


def _pick_price(sw: pd.DataFrame, method: str, close_1m: np.ndarray) -> np.ndarray:
    if method == "extreme":
        return sw["price_extreme"].to_numpy()
    if method == "close":
        return sw["price_close"].to_numpy()
    if method == "mid":
        return sw["price_mid"].to_numpy()
    if method == "reaction_price":
        # fechamento do minuto em que o extremo ocorreu: onde o mercado
        # efetivamente virou, sem o exagero da agulhada
        return close_1m[sw["pos"].to_numpy()]
    raise ValueError(f"event_price_method invalido: {method}")


def build_events(
    df: pd.DataFrame,
    cfg,
    atr_ref: np.ndarray,
    rel_vol: np.ndarray,
    tf_bars: Dict[str, pd.DataFrame] = None,
) -> pd.DataFrame:
    """Gera o DataFrame de eventos de todas as escalas e fontes."""
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    ts = df.index

    tables = build_excursion_tables(df, cfg.reaction_horizons)
    from config import TF_MINUTES
    ref_minutes = TF_MINUTES.get(cfg.atr_ref_tf, 60)

    tf_bars = tf_bars or {}
    chunks: List[pd.DataFrame] = []

    def _finish(raw: pd.DataFrame, scale: str, source: str):
        if raw.empty:
            return
        raw = raw.sort_values("pos", kind="mergesort")
        labels = _group_independent(
            raw["pos"].to_numpy(), raw["price"].to_numpy(),
            high, low, atr_ref, cfg.min_event_separation_atr,
        )
        ev = _collapse(raw, labels)
        pos = ev["pos"].to_numpy()
        reaction, strength, _ = measure(pos, ev["price"].to_numpy(), tables, atr_ref, ref_minutes)
        ev = ev.assign(
            timestamp=ts[pos],
            scale=scale,
            source=source,
            reaction=reaction,
            strength=strength,
            rel_volume=rel_vol[pos],
            atr=atr_ref[pos],
        )
        chunks.append(ev)

    # ------------------------------------------------------------ swings
    for rule, n in cfg.timeframes.items():
        bars = tf_bars.get(rule)
        if bars is None:
            bars = resample_ohlcv(df, rule)
            tf_bars[rule] = bars
        sw = find_swings(bars, n)
        if sw.empty:
            continue
        raw = pd.DataFrame({
            "pos": sw["pos"].to_numpy(),
            "price": _pick_price(sw, cfg.event_price_method, close),
        })
        _finish(raw, rule, "swing")

    # -------------------------------------------------- niveis conhecidos
    for rule in cfg.reference_periods:
        bars = tf_bars.get(rule)
        if bars is None:
            bars = resample_ohlcv(df, rule)
            tf_bars[rule] = bars
        refs = reference_events(bars, cfg.reference_kinds)
        for kind, sub in refs.groupby("kind"):
            raw = sub[["pos", "price"]].reset_index(drop=True)
            _finish(raw, f"ref_{rule}", f"ref_{kind}")

    if not chunks:
        return pd.DataFrame(columns=EVENT_COLUMNS)

    events = pd.concat(chunks, ignore_index=True)
    events = events[events["strength"] >= cfg.min_reaction_strength]
    events = events.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    return events[EVENT_COLUMNS + ["n_bars"]]


def event_weights(events: pd.DataFrame, cfg, ref_time: pd.Timestamp) -> np.ndarray:
    """Peso de cada evento: forca da reacao x escala x recencia x volume."""
    strength = np.minimum(events["strength"].to_numpy(), cfg.reaction_cap)
    tf_w = events["scale"].map(cfg.scale_weights).fillna(1.0).to_numpy()

    age_days = (ref_time - events["timestamp"]).dt.total_seconds().to_numpy() / 86400.0
    decay = np.exp(-np.maximum(age_days, 0.0) / max(cfg.recency_half_life_days, 1.0))
    decay = cfg.recency_floor + (1.0 - cfg.recency_floor) * decay

    rv = events["rel_volume"].to_numpy()
    vol_w = np.where(np.isfinite(rv), np.clip(rv, 0.25, 4.0) ** 0.5, 1.0)

    return strength * tf_w * decay * vol_w
