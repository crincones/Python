"""Construcao e pontuacao dos niveis (secoes 16 a 22 e 31).

O resultado e sempre PRECO + RELEVANCIA. Nunca uma zona, nunca um rotulo de
suporte ou resistencia.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from data.validation import normalize_to_tick
from models.level import Level
from scoring.confluence import confluence_stats
from scoring.recency import age_days, decay

# Faixa em que o score final e apresentado.
SCORE_MIN, SCORE_MAX = 25.0, 99.0


# ---------------------------------------------------------------- utilidades
def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values, kind="mergesort")
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    if cw[-1] <= 0:
        return float(np.median(values))
    return float(v[np.searchsorted(cw, 0.5 * cw[-1])])


def _rank01(values: np.ndarray) -> np.ndarray:
    """Percentil (0..1) robusto a outliers e a escalas incomparaveis."""
    v = np.asarray(values, dtype="float64")
    v = np.where(np.isfinite(v), v, np.nanmin(v) if np.isfinite(v).any() else 0.0)
    if v.size == 0:
        return v
    if np.allclose(v, v[0]):
        return np.full(v.size, 0.5)
    r = pd.Series(v).rank(method="average").to_numpy()
    return (r - 1.0) / (r.size - 1.0)


def _cluster_price(prices: np.ndarray, weights: np.ndarray, method: str,
                   fallback: Optional[float] = None) -> float:
    if method == "weighted_median":
        return weighted_median(prices, weights)
    if method == "median":
        return float(np.median(prices))
    if method == "mean":
        return float(np.mean(prices))
    if method == "weighted_mean":
        s = weights.sum()
        return float(np.average(prices, weights=weights)) if s > 0 else float(np.mean(prices))
    if method == "density":
        return float(fallback) if fallback is not None else weighted_median(prices, weights)
    raise ValueError(f"level_price_method invalido: {method}")


# ------------------------------------------------------------------- niveis
def build_levels(
    events: pd.DataFrame,
    weights: np.ndarray,
    labels: np.ndarray,
    cfg,
    tick: float,
    ref_time: pd.Timestamp,
    peaks: Optional[np.ndarray] = None,
) -> List[Level]:
    """Transforma clusters de eventos em niveis com estatisticas de suporte."""
    ev = events.assign(_w=weights, _lab=labels)
    ev = ev[ev["_lab"] >= 0]
    if ev.empty:
        return []

    ts = ev["timestamp"]
    ev = ev.assign(
        _day=ts.dt.normalize(),
        _week=ts.dt.to_period("W").astype(str),
        _month=ts.dt.to_period("M").astype(str),
        _decay=decay(age_days(ts, ref_time), cfg.recency_half_life_days, cfg.recency_floor),
    )

    levels: List[Level] = []
    for lab, sub in ev.groupby("_lab", sort=True):
        if len(sub) < cfg.min_events:
            continue

        prices = sub["price"].to_numpy()
        w = sub["_w"].to_numpy()
        fallback = float(peaks[lab]) if (peaks is not None and lab < len(peaks)) else None
        price = _cluster_price(prices, w, cfg.level_price_method, fallback)
        price = float(normalize_to_tick(price, tick))

        strength = np.minimum(sub["strength"].to_numpy(), cfg.reaction_cap)
        conf = confluence_stats(sub, cfg.scale_weights)
        span = (sub["timestamp"].max() - sub["timestamp"].min()).total_seconds() / 86400.0

        lv = Level(
            price=price,
            n_events=int(len(sub)),
            unique_days=int(sub["_day"].nunique()),
            unique_weeks=int(sub["_week"].nunique()),
            unique_months=int(sub["_month"].nunique()),
            span_days=float(span),
            first_event=sub["timestamp"].min(),
            last_event=sub["timestamp"].max(),
            mean_strength=float(strength.mean()),
            median_strength=float(np.median(strength)),
            max_strength=float(strength.max()),
            mean_reaction=float(sub["reaction"].mean()),
            n_scales=conf["n_scales"],
            n_sources=conf["n_sources"],
            mean_rel_volume=float(np.nanmean(sub["rel_volume"].to_numpy()))
            if np.isfinite(sub["rel_volume"].to_numpy()).any() else float("nan"),
            decayed_touches=float(sub["_decay"].sum()),
        )
        lv.components["_scale_weight"] = conf["scale_weight"]
        lv.components["_n_pairs"] = float(conf["n_pairs"])
        levels.append(lv)

    return score_levels(levels, cfg, ref_time)


def score_levels(levels: List[Level], cfg, ref_time: pd.Timestamp) -> List[Level]:
    """Score 0..100 combinando os fatores da secao 17.

    Cada fator bruto e convertido em percentil entre os niveis candidatos antes
    de ser combinado: isso evita que uma unica grandeza (por exemplo o numero de
    eventos) domine a soma so por ter magnitude maior.
    """
    if not levels:
        return []

    n_events = np.array([lv.n_events for lv in levels], dtype="float64")
    u_days = np.array([lv.unique_days for lv in levels], dtype="float64")
    u_months = np.array([lv.unique_months for lv in levels], dtype="float64")
    span = np.array([lv.span_days for lv in levels], dtype="float64")
    strength = np.array([0.6 * lv.mean_strength + 0.4 * lv.median_strength for lv in levels])
    max_strength = np.array([lv.max_strength for lv in levels])
    tf_w = np.array([lv.components["_scale_weight"] for lv in levels])
    pairs = np.array([lv.components["_n_pairs"] for lv in levels])
    rec = np.array([lv.decayed_touches for lv in levels])
    vol = np.array([lv.mean_rel_volume for lv in levels])
    last_age = np.array([(ref_time - lv.last_event).total_seconds() / 86400.0 for lv in levels])

    # secao 18: contagem entra em escala logaritmica; dias/meses distintos pesam
    # mais que eventos repetidos no mesmo pregao.
    comp = {
        "touch": _rank01(np.log1p(n_events)),
        "reaction": 0.75 * _rank01(strength) + 0.25 * _rank01(max_strength),
        "temporal": (0.45 * _rank01(np.log1p(u_days))
                     + 0.35 * _rank01(np.log1p(u_months))
                     + 0.20 * _rank01(span)),
        "scale": _rank01(tf_w),
        "volume": _rank01(vol) if np.isfinite(vol).any() else np.full(len(levels), 0.5),
        "recency": 0.7 * _rank01(rec) + 0.3 * _rank01(-last_age),
        "confluence": _rank01(pairs),
    }

    w = cfg.score_weights
    total_w = sum(w.values())
    total = np.zeros(len(levels))
    for k, v in comp.items():
        total += w.get(k, 0.0) * v
    total = total / max(total_w, 1e-9)

    # A soma de percentis se concentra em torno de 0.5; reescala para uma faixa
    # legivel (SCORE_MIN..SCORE_MAX). O score e, portanto, RELATIVO ao conjunto
    # de candidatos da rodada -- serve para ordenar, nao como medida absoluta.
    lo, hi = float(total.min()), float(total.max())
    spread = hi - lo
    if spread < 1e-9:
        scaled = np.full(total.size, 0.5 * (SCORE_MIN + SCORE_MAX))
    else:
        scaled = SCORE_MIN + (SCORE_MAX - SCORE_MIN) * (total - lo) / spread

    for i, lv in enumerate(levels):
        lv.score = float(round(scaled[i], 1))
        lv.components.update({k: float(round(v[i], 4)) for k, v in comp.items()})

    levels.sort(key=lambda x: x.score, reverse=True)
    return levels


# ------------------------------------------------------------------ selecao
def select_levels(
    levels: List[Level],
    cfg,
    separation: float,
    ref_price: Optional[float] = None,
) -> List[Level]:
    """Top N respeitando a separacao minima entre linhas (secoes 31 e 39.1).

    `separation` e a distancia MINIMA entre duas linhas. A janela de desenho
    (`window_points`) concentra as linhas na regiao util do grafico: por padrao
    `top_n * separation / 2` para cada lado do preco de referencia -- o espaco
    exato para acomodar `top_n` linhas na densidade pedida, de modo que a
    separacao MEDIA obtida fique proxima da pedida. Passando 0 o filtro e
    desligado e as linhas podem cobrir toda a faixa de precos do historico.

    Se a regiao nao contiver `top_n` niveis com evidencia suficiente, o
    resultado tem menos linhas -- por desenho, o algoritmo e conservador
    (secao 38).
    """
    picked: List[Level] = []
    lo = hi = None
    window = cfg.window_points
    if window is None:
        window = 0.5 * cfg.top_n * separation
    if ref_price and window > 0:
        lo, hi = ref_price - window, ref_price + window

    elegiveis = [lv for lv in sorted(levels, key=lambda x: x.score, reverse=True)
                 if lv.score >= cfg.min_score
                 and (lo is None or lo <= lv.price <= hi)]

    for lv in elegiveis:
        if any(abs(lv.price - p.price) < separation for p in picked):
            continue
        picked.append(lv)
        if len(picked) >= cfg.top_n:
            break

    picked = _fill_gaps(picked, elegiveis, cfg, separation)
    picked.sort(key=lambda x: x.price, reverse=True)
    return picked


def _fill_gaps(picked: List[Level], elegiveis: List[Level], cfg, separation: float) -> List[Level]:
    """Garante que nenhum vao entre linhas vizinhas passe de `cfg.max_gap`.

    A selecao por score sozinha deixa buracos: regiao onde o preco passou
    rapido pontua menos que uma consolidacao antiga, e o orcamento de `top_n`
    linhas se esgota antes. Aqui cada vao grande recebe o melhor candidato que
    couber dentro dele -- por isso o total pode passar de `top_n`, e passar e o
    comportamento desejado (a alternativa seria deixar o buraco).
    """
    if not cfg.max_gap or cfg.max_gap <= 0 or len(picked) < 2:
        return picked

    escolhidos = sorted(picked, key=lambda x: x.price)
    restantes = [lv for lv in elegiveis if lv not in escolhidos]
    sem_saida = set()

    for _ in range(500):
        precos = [lv.price for lv in escolhidos]
        vaos = [(precos[i + 1] - precos[i], i) for i in range(len(precos) - 1)]
        vaos = [(g, i) for g, i in vaos if g > cfg.max_gap and i not in sem_saida]
        if not vaos:
            break

        _, i = max(vaos)
        a, b = precos[i], precos[i + 1]
        dentro = [lv for lv in restantes
                  if a + separation <= lv.price <= b - separation
                  and all(abs(lv.price - p) >= separation for p in precos)]
        if not dentro:
            sem_saida.add(i)
            continue

        melhor = max(dentro, key=lambda x: x.score)
        restantes.remove(melhor)
        escolhidos.append(melhor)
        escolhidos.sort(key=lambda x: x.price)
        sem_saida = set()  # os indices mudaram

    return escolhidos
