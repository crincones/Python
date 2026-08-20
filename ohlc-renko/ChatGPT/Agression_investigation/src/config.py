"""
Configuracao central do projeto.

Todas as constantes usadas pelo pipeline vivem aqui para garantir
reprodutibilidade (secao 32 do CLAUDE.md).
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------- caminhos
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_CSV = Path(
    r"C:\Users\Carlos\Documents\GitHub\Python\ohlc-renko\WINFUT"
    r"\WINFUT_11R_AGB_AGS_BDURF_QT_TRD.csv"
)

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
RESULTS_DIR = PROJECT_ROOT / "results"
NTSL_DIR = PROJECT_ROOT / "ntsl"

for _d in (DATA_RAW, DATA_PROCESSED, MODELS_DIR, REPORTS_DIR, FIGURES_DIR,
           RESULTS_DIR, NTSL_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- ingestao
CSV_SEP = ";"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S.%f"

COLUMN_MAP = {
    "Data": "Date",
    "Abertura": "Open",
    "Máxima": "High",
    "Mínima": "Low",
    "Fechamento": "Close",
    "AgressionVolBuy": "AggBuy",
    "AgressionVolSell": "AggSell",
    "BarDurationF": "Duration",
    "Quantity": "Quantity",
    "Trades": "Trades",
}

# ---------------------------------------------------------------- numerica
# EPSILON: protecao contra divisao por zero.
# O WIN negocia em passos de 5 pontos; o Renko 11R tem brick nominal de
# 55 pontos. Um range so pode ser 0 ou >= 5 pontos. EPSILON = 1.0 e portanto
# menor que qualquer range real nao-nulo, e mantem a feature finita quando
# o range e exatamente zero (barra degenerada).
EPSILON = 1.0

# Tamanho do brick medido na propria base: |Close - Open| == 50.0 em
# 20000/20000 barras completas. NAO e 55 (11 * 5); o "11R" do nome nao
# corresponde ao tamanho efetivo do brick neste arquivo.
BRICK_SIZE = 50.0

# ---------------------------------------------------------------- features
# BarDurationF vem em MINUTOS x 1000 (confirmado pelo usuario e verificado:
# a barra de 24/07 18:31 tem Duration=3.752.167; x0,06 = 225.130 s, e o
# intervalo medido ate a barra seguinte foi 225.130,18 s — o fim de semana).
# Para converter em segundos: BarDurationF * 60 / 1000 = BarDurationF * 0,06.
DURATION_TO_SECONDS = 0.06

MA_PERIOD = 20          # periodo das medias moveis (DurationMA20 etc.)
DEFAULT_LAGS = 5        # numero de lags padrao
LAG_GRID = (3, 5, 8, 10)

LAGGED_FEATURES = [
    "AggBuyNorm",
    "AggSellNorm",
    "AggBalanceNorm",
    "AggTotalNorm",
    "QuantityNorm",
    "TradesNorm",
    "DurationResidual",
]

# ---------------------------------------------------------------- targets
PRE_SEQ_GRID = (2, 3)       # candles de pre-sequencia
CONT_GRID = (2, 3)          # candles de continuacao exigida
MAX_FUTURE_BARS = 3         # horizonte futuro dos targets de SEQUENCIA

# --- target em PONTOS (novo, pedido pelo usuario) -------------------------
# Sucesso = a partir do fechamento da barra de virada, atingir
# TARGET_POINTS pontos a favor ANTES de tocar o extremo oposto da propria
# barra de virada (Low[t] numa virada de alta, High[t] numa de baixa).
TARGET_POINTS = 100.0
POINTS_HORIZON = 50         # bricks para o evento resolver antes de timeout
# Empate dentro de uma mesma barra (toca alvo e stop): resolver pelo stop.
POINTS_PESSIMISTIC = True

# ---------------------------------------------------------------- validacao
N_FOLDS = 6
# Embargo dos targets de sequencia (usam no maximo t+3).
EMBARGO_BARS = 3            # >= MAX_FUTURE_BARS
# Embargo do target em pontos: um evento pode levar ate POINTS_HORIZON
# barras para resolver, entao o embargo precisa cobrir o horizonte inteiro,
# caso contrario treino e validacao compartilham eventos.
EMBARGO_BARS_POINTS = POINTS_HORIZON
MIN_TRAIN_FRACTION = 0.35   # fracao inicial da serie usada no 1o treino

# Holdout final: ultimos X% da serie, nunca usados para escolher threshold
# nem hiperparametros.
FINAL_TEST_FRACTION = 0.20

THRESHOLD_GRID = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80)

# ---------------------------------------------------------------- modelo
SEED = 42

CATBOOST_BASE_PARAMS = dict(
    loss_function="Logloss",
    eval_metric="AUC",
    random_seed=SEED,
    iterations=2000,
    od_type="Iter",
    od_wait=100,
    verbose=False,
    allow_writing_files=False,
)

CATBOOST_GRID = [
    dict(depth=d, learning_rate=lr, l2_leaf_reg=l2)
    for d in (3, 4, 5, 6)
    for lr in (0.02, 0.05, 0.10)
    for l2 in (3.0, 10.0)
]

os.environ.setdefault("PYTHONHASHSEED", str(SEED))
