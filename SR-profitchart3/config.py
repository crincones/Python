"""
Configuracao central do detector de niveis importantes.

Todos os parametros relevantes do projeto vivem aqui (secao 36 do descritivo).
Nenhum valor abaixo deve ser considerado otimo: sao pontos de partida.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Timeframes suportados. A chave e o alias de resample do pandas.
# ---------------------------------------------------------------------------
TF_MINUTES: Dict[str, float] = {
    "1min": 1,
    "5min": 5,
    "15min": 15,
    "30min": 30,
    "1h": 60,
    "4h": 240,
    "1D": 375,        # ~ pregao util do WIN (minutos negociados), usado so p/ escala
    "W-MON": 1875,
    "ME": 8000,
}


@dataclass
class Config:
    # ------------------------------------------------------------------ modo
    # renko -> analisa UM unico grafico Renko construido a partir do 1m
    # mtf    -> analisa varios tempos graficos (5m, 15m, 1h, 4h, 1D, semanal)
    mode: str = "renko"

    # ------------------------------------------------------------------ dados
    csv_path: str = "WIN$N_M1_202108120900_202608111824.csv"
    date_from: Optional[str] = None      # limite inicial do historico (inclusive)
    date_to: Optional[str] = None        # limite final do historico (inclusive)
    tick_size: Optional[float] = None    # None -> inferido a partir dos dados

    # ----------------------------------------------------------- volatilidade
    atr_period: int = 14
    atr_ref_tf: str = "1h"               # escala usada como referencia de regime
    vol_norm_window: int = 5000          # barras de 1m p/ normalizar volume

    # ------------------------------------------------------------- timeframes
    # alias de resample -> janela do fractal (n barras de cada lado)
    timeframes: Dict[str, int] = field(default_factory=lambda: {
        "5min": 4,
        "15min": 3,
        "1h": 3,
        "4h": 2,
        "1D": 2,
        "W-MON": 2,
    })
    # ----------------------------------------------------------------- renko
    # "50R" no ProfitChart = caixa de (50-1) ticks; a grade e ancorada em zero.
    # Conferido contra um export 50R real: caixa de 245 pts no WIN.
    renko_box_ticks: int = 50
    renko_box_points: Optional[float] = None   # sobrepoe renko_box_ticks
    renko_anchor: float = 0.0
    # preco do evento no renko: renko (linha da grade) | extreme (pavio real) | close
    renko_price_method: str = "renko"
    # horizontes da reacao, em TIJOLOS
    renko_horizons: List[int] = field(default_factory=lambda: [5, 10, 20, 40])
    # forca minima do giro: reacao / (caixa * sqrt(horizonte)).
    # 1.0 = o preco se afastou tanto quanto o acaso levaria; abaixo disso o
    # giro nao tem nada de especial.
    renko_min_strength: float = 1.30
    # dois giros no mesmo preco sao o mesmo evento ate o mercado se afastar
    renko_merge_boxes: float = 0.5
    renko_departure_boxes: float = 2.0
    # banda de agrupamento, em caixas
    cluster_box_factor: float = 0.35

    # peso estrutural de cada escala no score.
    # No modo renko a "escala" e a PROFUNDIDADE do pivo (d1 = giro de 1 tijolo,
    # d8 = giro de 8 ou mais): e ela que substitui a hierarquia de timeframes.
    scale_weights: Dict[str, float] = field(default_factory=lambda: {
        "d1": 0.50,
        "d2": 0.80,
        "d3": 1.20,
        "d5": 1.80,
        "d8": 2.50,
        # usados apenas no modo mtf
        "5min": 0.55,
        "15min": 0.75,
        "1h": 1.00,
        "4h": 1.40,
        "1D": 1.90,
        # "W-MON": 2.40,
        # "ref_1D": 1.60,
        # "ref_W-MON": 2.10,
        # "ref_ME": 2.60,
    })

    # ---------------------------------------------------- niveis de referencia
    # (secao 24) maxima/minima/abertura/fechamento de dia, semana e mes
    reference_periods: List[str] = field(default_factory=lambda: ["1D", "W-MON", "ME"])
    reference_kinds: List[str] = field(default_factory=lambda: ["high", "low", "close", "open"])

    # ------------------------------------------------------------- eventos
    # preco representativo do evento: extreme | close | mid | reaction_price
    event_price_method: str = "reaction_price"
    # separacao minima entre eventos independentes, em ATR (secao 8)
    min_event_separation_atr: float = 0.5
    # horizontes de medicao da reacao, em minutos (secao 10)
    reaction_horizons: List[int] = field(default_factory=lambda: [5, 15, 30, 60, 240])
    # reacao minima (em multiplos do movimento esperado p/ o horizonte) p/ manter o evento
    min_reaction_strength: float = 0.70
    # teto aplicado a forca da reacao para evitar dominancia de outliers
    reaction_cap: float = 4.0

    # ----------------------------------------------------------- clustering
    # kde | dbscan | hierarchical
    cluster_method: str = "kde"
    # espaco em que os precos sao agrupados: linear (caixa fixa em pontos, modo
    # renko) ou log (tolerancia relativa, modo mtf)
    cluster_space: str = "linear"
    # eps/banda = cluster_atr_factor * ATR relativo mediano
    cluster_atr_factor: float = 0.20
    min_events: int = 6
    # preco final do cluster: weighted_median | median | mean | weighted_mean | density
    level_price_method: str = "weighted_median"
    # a banda nunca passa de `band_separation_ratio * separacao pedida`, senao o
    # KDE nao resolve niveis tao proximos quanto o usuario pediu
    band_separation_ratio: float = 0.30
    # distancia minima entre picos de densidade, em fracao da separacao pedida
    peak_distance_ratio: float = 0.60
    kde_grid: int = 40000
    kde_prominence: float = 0.005        # fracao da densidade maxima
    kde_assign_factor: float = 1.20      # raio de atribuicao, em bandas

    # --------------------------------------------------------------- scoring
    recency_half_life_days: float = 240.0
    recency_floor: float = 0.15          # piso do decaimento (secao 20)
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        "touch": 0.16,
        "reaction": 0.22,
        "temporal": 0.18,
        "scale": 0.12,
        "volume": 0.07,
        "recency": 0.13,
        "confluence": 0.12,
    })

    # --------------------------------------------------------------- selecao
    top_n: int = 20
    min_score: float = 0.0
    # separacao media desejada entre linhas, em pontos (secao 39.1).
    # None -> derivada da volatilidade (0.75 * ATR de referencia mediano)
    level_separation: Optional[float] = None
    # janela de desenho: +- X pontos em torno do ultimo fechamento.
    # None -> automatica (top_n * separacao / 2), o que faz a separacao media
    # entre as linhas desenhadas coincidir com a pedida pelo usuario.
    # 0 -> sem restricao (as linhas podem cobrir todo o historico de precos).
    window_points: Optional[float] = None
    # centro da janela de desenho. None -> ultimo fechamento do historico.
    reference_price: Optional[float] = None
    # vao maximo tolerado entre duas linhas vizinhas, em pontos. Vaos maiores
    # sao preenchidos com o melhor candidato disponivel, mesmo que isso passe
    # de top_n linhas. 0/None = sem garantia de cobertura.
    max_gap: Optional[float] = None

    # ----------------------------------------------------------------- saida
    out_dir: str = "output"
    ntsl_color_rgb: tuple = (0, 90, 255)
    ntsl_width: int = 1
    ntsl_style: int = 1                  # 0=solida 1=tracejada 2=pontilhada 3=traco-ponto
    ntsl_text_size: int = 9
    ntsl_text_pos: int = 0
    chart_tf: str = "1D"                 # timeframe usado no grafico de inspecao
    chart_last_days: int = 420           # 0 = plota todo o historico

    # -------------------------------------------------------------- execucao
    cache: bool = True
    cache_dir: str = ".cache"
    seed: int = 7

    # -------------------------------------------------------------- helpers
    def fingerprint(self) -> str:
        """Hash dos parametros que afetam a etapa de deteccao de eventos.

        Permite reaproveitar eventos ja calculados quando somente o score ou a
        selecao mudam (secao 35).
        """
        keys = [
            "mode", "csv_path", "date_from", "date_to", "tick_size", "atr_period",
            "atr_ref_tf", "vol_norm_window", "timeframes", "reference_periods",
            "reference_kinds", "event_price_method", "min_event_separation_atr",
            "reaction_horizons", "min_reaction_strength",
            "renko_box_ticks", "renko_box_points", "renko_anchor",
            "renko_price_method", "renko_horizons", "renko_min_strength",
            "renko_merge_boxes", "renko_departure_boxes",
        ]
        payload = {k: asdict(self)[k] for k in keys}
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha1(raw.encode()).hexdigest()[:12]
