"""Orquestracao das etapas: preprocessing -> eventos -> clustering -> scoring.

As etapas sao independentes de proposito (secao 35): mudar o score nao obriga a
reprocessar os candles, e o resultado intermediario de eventos pode ser
reaproveitado via cache.

Dois modos de deteccao de eventos:

  * `renko` (padrao) -- constroi UM grafico Renko a partir dos candles de 1
    minuto e analisa somente ele. A estrutura vem dos giros do proprio Renko e
    tudo e medido em caixas;
  * `mtf` -- a analise multi-timeframe (5m ... semanal) com niveis de
    referencia diarios/semanais/mensais.
"""

from __future__ import annotations

import os
import pickle
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from clustering import cluster_events
from data.loader import load_candles
from data.renko import box_from_ticks, build_renko
from data.resampling import atr_reference, relative_volume, resample_ohlcv
from data.validation import prepare
from detection.events import build_events, event_weights
from detection.renko_events import build_renko_events
from models.level import Level
from scoring.score import build_levels, select_levels


@dataclass
class Detection:
    """Saida da etapa cara (eventos), passivel de cache."""
    events: pd.DataFrame
    atr_ref: np.ndarray
    rel_vol: np.ndarray
    bricks: Optional[pd.DataFrame] = None
    box: float = 0.0


@dataclass
class Result:
    df: pd.DataFrame
    tick: float
    detection: Detection
    weights: np.ndarray
    labels: np.ndarray
    levels: List[Level]
    selected: List[Level]
    separation: float
    info: Dict = field(default_factory=dict)

    @property
    def events(self) -> pd.DataFrame:
        return self.detection.events


def load_and_prepare(cfg):
    """Carrega, valida e normaliza o historico de 1 minuto."""
    raw = load_candles(cfg.historico, cfg.date_from, cfg.date_to)
    df, tick, report = prepare(raw, cfg.tick_size)
    return df, tick, report


def renko_box(cfg, tick: float) -> float:
    return float(cfg.renko_box_points or box_from_ticks(cfg.renko_box_ticks, tick))


def detect_events(df: pd.DataFrame, cfg, tick: float, use_cache: bool = False) -> Detection:
    """Etapa cara: renko/ATR, giros ou swings, e reacoes."""
    cache_path = None
    if use_cache and cfg.cache:
        os.makedirs(cfg.cache_dir, exist_ok=True)
        cache_path = os.path.join(cfg.cache_dir, f"events_{cfg.fingerprint()}.pkl")
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as fh:
                return pickle.load(fh)

    rel_vol = relative_volume(df, cfg.vol_norm_window)

    if cfg.mode == "renko":
        box = renko_box(cfg, tick)
        bricks = build_renko(df, box, cfg.renko_anchor)
        events = build_renko_events(bricks, df, cfg, rel_vol, box)
        # no Renko a caixa E a unidade de volatilidade; o ATR so serve para a
        # validacao estatistica, que continua sendo feita no grafico de 1m
        atr_ref = np.full(len(df), box)
        det = Detection(events, atr_ref, rel_vol, bricks, box)
    else:
        ref_bars = resample_ohlcv(df, cfg.atr_ref_tf)
        atr_ref = atr_reference(df, ref_bars, cfg.atr_period)
        events = build_events(df, cfg, atr_ref, rel_vol)
        det = Detection(events, atr_ref, rel_vol, None, 0.0)

    if cache_path:
        with open(cache_path, "wb") as fh:
            pickle.dump(det, fh, protocol=4)
    return det


def run_pipeline(
    df: pd.DataFrame,
    cfg,
    tick: float,
    use_cache: bool = False,
    precomputed: Optional[Detection] = None,
) -> Result:
    det = precomputed or detect_events(df, cfg, tick, use_cache)
    events = det.events

    ref_time = df.index[-1]
    ref_price = float(cfg.reference_price or df["close"].iloc[-1])

    if events.empty:
        return Result(df, tick, det, np.array([]), np.array([]), [], [], 0.0,
                      {"n_clusters": 0, "n_niveis": 0, "n_selecionados": 0})

    weights = event_weights(events, cfg, ref_time)

    if cfg.mode == "renko":
        # tudo em pontos: a caixa nao muda ao longo do historico
        box = det.box
        band = cfg.cluster_box_factor * box
        separation = cfg.level_separation or box
        space = "linear"
        band_pts = band
    else:
        rel_atr = float(np.median(det.atr_ref / df["close"].to_numpy()))
        band = cfg.cluster_atr_factor * rel_atr
        separation = cfg.level_separation or 0.75 * float(np.median(det.atr_ref))
        med_price = float(np.median(df["close"].to_numpy()))
        # a banda tambem limita a RESOLUCAO: dois niveis separados por
        # `separation` so aparecem como picos distintos se o nucleo for bem
        # mais estreito que isso
        band = min(band, cfg.band_separation_ratio * separation / med_price)
        space = "log"
        band_pts = band * med_price

    min_distance = cfg.peak_distance_ratio * separation
    if space == "log":
        min_distance = min_distance / float(np.median(df["close"].to_numpy()))

    labels, info = cluster_events(
        events["price"].to_numpy(), weights, cfg, band, min_distance, space=space,
        grid_step=det.box,
    )

    levels = build_levels(events, weights, labels, cfg, tick, ref_time,
                          peaks=info.get("peaks"))
    selected = select_levels(levels, cfg, separation, ref_price=ref_price)

    info.update({
        "band_pts": band_pts,
        "separation": separation,
        "ref_price": ref_price,
        "n_eventos": int(len(events)),
        "n_niveis": len(levels),
        "n_selecionados": len(selected),
    })
    return Result(df, tick, det, weights, labels, levels, selected, separation, info)
