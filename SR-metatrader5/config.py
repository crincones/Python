"""
Configuracao central do detector de niveis importantes -- versao MetaTrader 5.

Mesmo motor do SR-profitchart3, com tres diferencas de fundo:

  * a entrada e o CSV de 1 minuto mantido pelo projeto baixar-ohlc-fx (mesmo
    formato de export do MT5, tab-separado);
  * o ativo pode ter preco fracionario (USDJPY tem digits=3), entao nada aqui
    assume preco inteiro -- as distancias sao expressas em PONTOS DO MT5
    (1 ponto = 1 tick = 10^-digits) e convertidas para unidades de preco
    depois que o tick e inferido a partir dos dados;
  * a saida e um CSV por simbolo gravado direto na pasta MQL5/Files do
    terminal, lido pelo indicador SR_Levels.mq5.

Nenhum valor abaixo deve ser considerado otimo: sao pontos de partida.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Caminhos fixos desta maquina.
#
# HISTORICO_DIR  : onde o baixar-ohlc-fx mantem os CSV de 1 minuto.
# MQL5_FILES_DIR : pasta Files do terminal (a "sandbox" que o MQL5 enxerga em
#                  FileOpen sem FILE_COMMON). Confira em Arquivo > Abrir pasta
#                  de dados > MQL5 > Files.
# MQL5_INDICATORS_DIR : destino do SR_Levels.mq5 quando se usa --instalar.
# ---------------------------------------------------------------------------
HISTORICO_DIR = r"C:\Users\Carlos\Documents\GitHub\Python\baixar-ohlc-fx"
MT5_DATA_DIR = r"C:\Users\Carlos\AppData\Roaming\MetaQuotes\Terminal\Metatrader5FX"
MQL5_FILES_DIR = os.path.join(MT5_DATA_DIR, "MQL5", "Files")
MQL5_INDICATORS_DIR = os.path.join(MT5_DATA_DIR, "MQL5", "Indicators")

# Caracteres proibidos em nome de arquivo no Windows. O indicador aplica a
# mesma substituicao ao _Symbol antes de montar o nome do arquivo.
INVALIDOS = '<>:"/\\|?*'


def sanitize_symbol(symbol: str) -> str:
    """Nome de arquivo seguro para um simbolo ("WIN$N" -> "WIN$N", "EUR/USD" -> "EUR_USD")."""
    return "".join("_" if c in INVALIDOS else c for c in symbol)


def historico_csv(symbol: str) -> str:
    """Caminho do CSV de 1 minuto mantido pelo baixar-ohlc-fx."""
    return os.path.join(HISTORICO_DIR, f"{sanitize_symbol(symbol)}_M1.csv")


# ---------------------------------------------------------------------------
# Timeframes suportados. A chave e o alias de resample do pandas.
# Os minutos servem so como escala relativa entre timeframes; o mercado de FX
# roda 24h, entao o dia vale 1440 minutos (no WIN valia ~375, o pregao util).
# ---------------------------------------------------------------------------
TF_MINUTES: Dict[str, float] = {
    "1min": 1,
    "5min": 5,
    "15min": 15,
    "30min": 30,
    "1h": 60,
    "4h": 240,
    "1D": 1440,
    "W-MON": 7200,
    "ME": 31000,
}


@dataclass
class Config:
    # ------------------------------------------------------------------ modo
    # renko -> analisa UM unico grafico Renko construido a partir do 1m
    # mtf    -> analisa varios tempos graficos (5m, 15m, 1h, 4h, 1D, semanal)
    mode: str = "renko"

    # ------------------------------------------------------------------ dados
    symbol: str = "USDJPY"
    csv_path: Optional[str] = None       # None -> historico_csv(symbol)
    date_from: Optional[str] = None      # limite inicial do historico (inclusive)
    date_to: Optional[str] = None        # limite final do historico (inclusive)
    tick_size: Optional[float] = None    # None -> inferido a partir dos dados
    digits: Optional[int] = None         # None -> derivado do tick inferido

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
    # Aqui a caixa vale renko_box_ticks * tick EXATOS -- nao existe a convencao
    # "NR = (N-1) ticks" do ProfitChart, que era especifica daquela plataforma.
    # USDJPY: tick = 0.001, entao 50 ticks = 0.050 (5 pips).
    renko_box_ticks: int = 50
    renko_box_points: Optional[float] = None   # em unidades de preco; sobrepoe os ticks
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
    })

    # ---------------------------------------------------- niveis de referencia
    # maxima/minima/abertura/fechamento de dia, semana e mes
    reference_periods: List[str] = field(default_factory=lambda: ["1D", "W-MON", "ME"])
    reference_kinds: List[str] = field(default_factory=lambda: ["high", "low", "close", "open"])

    # ------------------------------------------------------------- eventos
    # preco representativo do evento: extreme | close | mid | reaction_price
    event_price_method: str = "reaction_price"
    # separacao minima entre eventos independentes, em ATR
    min_event_separation_atr: float = 0.5
    # horizontes de medicao da reacao, em minutos
    reaction_horizons: List[int] = field(default_factory=lambda: [5, 15, 30, 60, 240])
    # reacao minima (em multiplos do movimento esperado p/ o horizonte)
    min_reaction_strength: float = 0.70
    # teto aplicado a forca da reacao para evitar dominancia de outliers
    reaction_cap: float = 4.0

    # ----------------------------------------------------------- clustering
    # kde | grade | dbscan | hierarchical
    cluster_method: str = "kde"
    # espaco em que os precos sao agrupados: linear (caixa fixa, modo renko) ou
    # log (tolerancia relativa, modo mtf)
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
    recency_floor: float = 0.15
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
    # ATENCAO: os tres campos abaixo vivem em UNIDADES DE PRECO. A linha de
    # comando os recebe em pontos do MT5 e main.py faz a conversao assim que o
    # tick e conhecido (veja aplicar_pontos()).
    top_n: int = 20
    min_score: float = 0.0
    # separacao media desejada entre linhas.
    # None -> derivada da volatilidade (a propria caixa, no modo renko)
    level_separation: Optional[float] = None
    # janela de desenho: +- X em torno do preco de referencia.
    # None -> automatica (top_n * separacao / 2); 0 -> sem restricao.
    window_points: Optional[float] = None
    # centro da janela de desenho. None -> ultimo fechamento do historico.
    reference_price: Optional[float] = None
    # vao maximo tolerado entre duas linhas vizinhas. Vaos maiores sao
    # preenchidos com o melhor candidato disponivel, mesmo passando de top_n.
    max_gap: Optional[float] = None

    # ----------------------------------------------------------------- saida
    out_dir: str = os.path.join(BASE_DIR, "output")
    # pasta Files do terminal; None desliga a copia (grava so em out_dir)
    mql5_files_dir: Optional[str] = MQL5_FILES_DIR
    csv_prefix: str = "SR_"              # SR_USDJPY.csv
    csv_sep: str = ";"
    chart_tf: str = "1D"                 # timeframe usado no grafico de inspecao
    chart_last_days: int = 420           # 0 = plota todo o historico

    # -------------------------------------------------------------- execucao
    cache: bool = True
    cache_dir: str = os.path.join(BASE_DIR, ".cache")
    seed: int = 7

    # -------------------------------------------------------------- helpers
    @property
    def historico(self) -> str:
        """CSV de entrada efetivo."""
        return self.csv_path or historico_csv(self.symbol)

    @property
    def csv_name(self) -> str:
        """Nome do arquivo lido pelo indicador."""
        return f"{self.csv_prefix}{sanitize_symbol(self.symbol)}.csv"

    def fingerprint(self) -> str:
        """Hash dos parametros que afetam a etapa de deteccao de eventos.

        Permite reaproveitar eventos ja calculados quando somente o score ou a
        selecao mudam.
        """
        keys = [
            "mode", "symbol", "csv_path", "date_from", "date_to", "tick_size",
            "atr_period", "atr_ref_tf", "vol_norm_window", "timeframes",
            "reference_periods", "reference_kinds", "event_price_method",
            "min_event_separation_atr", "reaction_horizons", "min_reaction_strength",
            "renko_box_ticks", "renko_box_points", "renko_anchor",
            "renko_price_method", "renko_horizons", "renko_min_strength",
            "renko_merge_boxes", "renko_departure_boxes",
        ]
        payload = {k: asdict(self)[k] for k in keys}
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha1(raw.encode()).hexdigest()[:12]
