"""
Feature engineering.

REGRA ABSOLUTA (secao 3 do CLAUDE.md): toda feature aqui usa exclusivamente
informacao de t, t-1, t-2, ... Nenhuma funcao deste modulo pode olhar para
t+1 ou adiante. Isso e verificado automaticamente por
``tests/test_no_lookahead.py`` / ``src/leakage_test.py``.

Convencoes:
  - ``.shift(k)`` com k > 0 = passado. ``.shift(-k)`` E PROIBIDO neste arquivo.
  - ``.rolling(n)`` do pandas e causal (janela terminando em t).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import (BRICK_SIZE, DEFAULT_LAGS, DURATION_TO_SECONDS, EPSILON,
                    LAGGED_FEATURES, MA_PERIOD)

# Grupos de features, usados pelos experimentos BASE / EXTENDED.
GROUP_BASE_CORE = [
    "AggBuyNorm", "AggSellNorm", "AggBalanceNorm", "AggTotalNorm",
    "QuantityNorm", "TradesNorm", "DurationResidual",
]

GROUP_STRUCTURE = [
    "Range", "BodyNorm", "Direction", "CloseLocation", "OpenLocation",
    "UpperWickNorm", "LowerWickNorm", "WickTotalNorm", "WickAsym",
]

GROUP_AGGRESSION_EXTRA = [
    "AggImbalance", "BuyShare", "SellShare",
    "AggBalanceChange", "AggBalanceAcceleration",
    "AggImbalanceChange", "DirVsAggDivergence", "AggPerBrickProgress",
]

GROUP_VOLUME = [
    "QuantityPerTrade", "TradesPerQuantity", "AggTotalPerQuantity",
    "AggTotalPerTrade", "AggShareOfQuantity",
    "QuantityResidual20", "TradesResidual20", "AggTotalResidual20",
    "QuantityRatio20", "TradesRatio20", "AggTotalRatio20",
    "QuantityPerTradeRatio20",
]

GROUP_CONTEXT = [
    "ConsecutiveUpCount", "ConsecutiveDownCount", "RunLength", "SignedRunLength",
    "BodyNormMean3", "BodyNormMean5",
    "AggBalanceNormMean3", "AggBalanceNormMean5",
    "AggTotalNormMean3", "AggTotalNormMean5",
    "DurationResidualMean3", "DurationResidualMean5",
    "CloseChange1Bricks", "CloseChange2Bricks", "CloseChange3Bricks",
    "RangeMean5", "RangeRatio20",
    "AggBalanceRunSum", "AggBalanceNormMean3Change",
]

GROUP_TIME_EXTRA = [
    "DurationRatio20", "DurationResidualPct", "LogDuration",
    "LogDurationResidual20", "DeltaTLog", "SecondsSinceSessionOpen",
    "HourOfDay",
]


# ------------------------------------------------------------------ helpers
def _safe_div(a, b, eps=EPSILON):
    return a / np.maximum(b, eps)


def _causal_mean(s: pd.Series, n: int) -> pd.Series:
    """Media movel simples causal: janela [t-n+1 .. t]."""
    return s.rolling(n, min_periods=n).mean()


# --------------------------------------------------------------- principal
def build_features(df: pd.DataFrame, ma_period: int = MA_PERIOD) -> pd.DataFrame:
    """Constroi todas as features contemporaneas (sem lags).

    ``df`` deve estar em ordem cronologica ascendente.
    """
    f = df.copy()

    o, h, l, c = f["Open"], f["High"], f["Low"], f["Close"]
    buy, sell = f["AggBuy"], f["AggSell"]
    qty, trd, dur = f["Quantity"], f["Trades"], f["Duration"]

    # ---------------------------------------------------------- secao 4
    f["Range"] = h - l
    rng = np.maximum(f["Range"], EPSILON)          # RangeSafe
    f["RangeSafe"] = rng

    f["AggTotal"] = buy + sell
    f["AggBalance"] = buy - sell

    f["AggBuyNorm"] = buy / rng
    f["AggSellNorm"] = sell / rng
    f["AggBalanceNorm"] = (buy - sell) / rng
    f["AggTotalNorm"] = (buy + sell) / rng
    f["QuantityNorm"] = qty / rng
    f["TradesNorm"] = trd / rng

    # ---------------------------------------------------------- secao 5
    f["DurationMA20"] = _causal_mean(dur, ma_period)
    f["DurationResidual"] = dur - f["DurationMA20"]
    f["DurationRatio20"] = _safe_div(dur, f["DurationMA20"])
    f["DurationResidualPct"] = _safe_div(dur - f["DurationMA20"],
                                         f["DurationMA20"])
    # Segundos de relogio: BarDurationF esta em minutos x 1000.
    f["DurationSec"] = dur * DURATION_TO_SECONDS
    # Versoes robustas: a ULTIMA barra de cada pregao so fecha quando o
    # pregao seguinte se move, entao a duracao dela abrange a madrugada ou
    # o fim de semana e chega a 4 ordens de grandeza acima da mediana.
    # Sao valores legitimos, nao sujeira — mas destroem media e residuo.
    f["LogDuration"] = np.log1p(dur)
    f["LogDurationResidual20"] = (
        f["LogDuration"] - _causal_mean(f["LogDuration"], ma_period)
    )

    # tempo de relogio — disponivel no fechamento de t, portanto causal
    dt = f["Date"].diff().dt.total_seconds()
    f["DeltaTSec"] = dt
    f["DeltaTLog"] = np.log1p(dt.clip(lower=0))
    session = f["Date"].dt.normalize()
    f["SecondsSinceSessionOpen"] = (
        f["Date"] - f.groupby(session)["Date"].transform("min")
    ).dt.total_seconds()
    f["HourOfDay"] = f["Date"].dt.hour + f["Date"].dt.minute / 60.0

    # ---------------------------------------------------------- secao 7
    body = c - o
    f["Body"] = body
    f["BodyAbs"] = body.abs()
    f["BodyNorm"] = body.abs() / rng
    f["Direction"] = np.sign(body).astype(int)
    f["CloseLocation"] = (c - l) / rng
    f["OpenLocation"] = (o - l) / rng

    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - l
    f["UpperWick"] = upper
    f["LowerWick"] = lower
    f["UpperWickNorm"] = upper / rng
    f["LowerWickNorm"] = lower / rng
    f["WickTotalNorm"] = (upper + lower) / rng
    f["WickAsym"] = (upper - lower) / rng

    # ---------------------------------------------------------- secao 8
    tot_safe = np.maximum(f["AggTotal"], EPSILON)
    f["AggImbalance"] = (buy - sell) / tot_safe
    f["BuyShare"] = buy / tot_safe
    f["SellShare"] = sell / tot_safe
    f["AggBalanceChange"] = f["AggBalanceNorm"].diff()
    f["AggBalanceAcceleration"] = f["AggBalanceChange"].diff()
    f["AggImbalanceChange"] = f["AggImbalance"].diff()
    # divergencia: candle sobe mas saldo agressor e vendedor (e vice-versa)
    f["DirVsAggDivergence"] = (
        (np.sign(f["AggImbalance"]) != f["Direction"]).astype(int)
        * f["AggImbalance"].abs()
        * -f["Direction"]
    )
    # agressao gasta por brick de progresso liquido (esforco x resultado)
    f["AggPerBrickProgress"] = f["AggTotal"] / BRICK_SIZE

    # ---------------------------------------------------------- secao 9
    f["QuantityPerTrade"] = qty / np.maximum(trd, 1)
    f["TradesPerQuantity"] = trd / np.maximum(qty, 1)
    f["AggTotalPerQuantity"] = f["AggTotal"] / np.maximum(qty, 1)
    f["AggTotalPerTrade"] = f["AggTotal"] / np.maximum(trd, 1)
    f["AggShareOfQuantity"] = f["AggTotalPerQuantity"]

    for name, src in (("Quantity", qty), ("Trades", trd),
                      ("AggTotal", f["AggTotal"])):
        ma = _causal_mean(src, ma_period)
        f[f"{name}MA20"] = ma
        f[f"{name}Residual20"] = src - ma
        f[f"{name}Ratio20"] = _safe_div(src, ma)

    f["QuantityPerTradeRatio20"] = _safe_div(
        f["QuantityPerTrade"], _causal_mean(f["QuantityPerTrade"], ma_period)
    )
    f["RangeMean5"] = _causal_mean(f["Range"], 5)
    f["RangeRatio20"] = _safe_div(f["Range"], _causal_mean(f["Range"], ma_period))

    # --------------------------------------------------------- secao 10
    d = f["Direction"]
    # run corrente terminando em t (inclui t)
    run_id = (d != d.shift(1)).cumsum()
    run_len = d.groupby(run_id).cumcount() + 1
    f["RunLength"] = run_len
    f["SignedRunLength"] = run_len * d
    f["ConsecutiveUpCount"] = np.where(d > 0, run_len, 0)
    f["ConsecutiveDownCount"] = np.where(d < 0, run_len, 0)

    for n in (3, 5):
        f[f"BodyNormMean{n}"] = _causal_mean(f["BodyNorm"], n)
        f[f"AggBalanceNormMean{n}"] = _causal_mean(f["AggBalanceNorm"], n)
        f[f"AggTotalNormMean{n}"] = _causal_mean(f["AggTotalNorm"], n)
        f[f"DurationResidualMean{n}"] = _causal_mean(f["DurationResidual"], n)
    f["AggBalanceNormMean3Change"] = f["AggBalanceNormMean3"].diff()

    for k in (1, 2, 3):
        f[f"CloseChange{k}Bricks"] = (c - c.shift(k)) / BRICK_SIZE

    # saldo de agressao acumulado dentro do run corrente (somente ate t)
    f["AggBalanceRunSum"] = (
        f["AggBalanceNorm"].groupby(run_id).cumsum()
    )

    # --------------------------------------------------------- diagnostico
    f["IsSyntheticBrick"] = ((qty == 0) & (trd == 0)).astype(int)
    f["IsSessionFirstBar"] = (session != session.shift(1)).astype(int)

    return f


# ------------------------------------------- relacoes t vs t-1 (secao 8bis)
# Todas as features NORMALIZADAS (razoes/proporcoes, nao niveis brutos)
# ganham a comparacao explicita contra a barra anterior. Motivacao: um
# modelo de arvore com eixos alinhados nao representa bem a fronteira
# diagonal "X[t] > X[t-1]" mesmo tendo X e X_lag1 disponiveis.
NORMALIZED_FOR_COMPARISON = [
    # agressao normalizada pelo range
    "AggBuyNorm", "AggSellNorm", "AggBalanceNorm", "AggTotalNorm",
    # volume/negocios normalizados pelo range
    "QuantityNorm", "TradesNorm",
    # estrutura do candle (ja em fracao do range)
    "BodyNorm", "UpperWickNorm", "LowerWickNorm", "WickTotalNorm", "WickAsym",
    # proporcoes de agressao
    "AggImbalance", "BuyShare", "SellShare",
    # razoes de atividade
    "QuantityPerTrade", "TradesPerQuantity", "AggTotalPerQuantity",
    "AggTotalPerTrade",
    # razoes contra a media movel de 20
    "RangeRatio20", "AggTotalRatio20", "QuantityRatio20", "TradesRatio20",
    "QuantityPerTradeRatio20", "DurationRatio20",
    # tempo, versao robusta
    "LogDurationResidual20",
]

# Features que trocam de sinal: a RAZAO t/t-1 nao e interpretavel nelas
# (dividir por um numero negativo inverte a ordem, e perto de zero explode).
# Para essas emitimos apenas '>', '<' e a diferenca.
SIGN_CHANGING = {
    "AggBalanceNorm", "WickAsym", "AggImbalance", "LogDurationResidual20",
}


def add_prev_comparisons(f: pd.DataFrame, cols=None) -> pd.DataFrame:
    """Adiciona, para cada feature normalizada X:

        X_gt_prev  = 1 se X[t] >  X[t-1]      (booleano pedido)
        X_lt_prev  = 1 se X[t] <  X[t-1]      (booleano pedido)
        X_chg1     = X[t] - X[t-1]            (magnitude da mudanca)
        X_ratio1   = X[t] / X[t-1]            (so para X sempre >= 0)

    ``gt`` e ``lt`` NAO sao complementares: ambos sao 0 no empate
    (frequente em barras com agressao zero), entao os dois carregam
    informacao e ambos foram pedidos explicitamente.

    CAUSAL: usa somente t e t-1.
    """
    cols = list(NORMALIZED_FOR_COMPARISON if cols is None else cols)
    new = {}
    for c in cols:
        if c not in f.columns:
            raise KeyError(f"feature normalizada ausente: {c}")
        cur = f[c]
        prev = cur.shift(1)
        valid = prev.notna()
        new[f"{c}_gt_prev"] = (cur > prev).astype(float).where(valid)
        new[f"{c}_lt_prev"] = (cur < prev).astype(float).where(valid)
        new[f"{c}_chg1"] = cur - prev
        if c not in SIGN_CHANGING:
            denom = prev.where(prev.abs() > EPSILON * 1e-6)
            new[f"{c}_ratio1"] = cur / denom
    return pd.concat([f, pd.DataFrame(new, index=f.index)], axis=1)


def prev_comparison_names(cols=None, include_ratio: bool = True) -> list[str]:
    cols = list(NORMALIZED_FOR_COMPARISON if cols is None else cols)
    out = []
    for c in cols:
        out += [f"{c}_gt_prev", f"{c}_lt_prev", f"{c}_chg1"]
        if include_ratio and c not in SIGN_CHANGING:
            out.append(f"{c}_ratio1")
    return out


def add_lags(f: pd.DataFrame, cols=None, n_lags: int = DEFAULT_LAGS) -> pd.DataFrame:
    """Adiciona X_t-1 .. X_t-n_lags. Somente shift positivo (passado)."""
    cols = list(LAGGED_FEATURES if cols is None else cols)
    new = {}
    for col in cols:
        if col not in f.columns:
            raise KeyError(f"coluna para lag ausente: {col}")
        for k in range(1, n_lags + 1):
            new[f"{col}_lag{k}"] = f[col].shift(k)
    return pd.concat([f, pd.DataFrame(new, index=f.index)], axis=1)


def lag_names(cols=None, n_lags: int = DEFAULT_LAGS) -> list[str]:
    cols = list(LAGGED_FEATURES if cols is None else cols)
    return [f"{c}_lag{k}" for c in cols for k in range(1, n_lags + 1)]


def feature_set(name: str, n_lags: int = DEFAULT_LAGS) -> list[str]:
    """Retorna a lista de colunas de cada conjunto de features."""
    if name == "BASE":
        return GROUP_BASE_CORE + lag_names(GROUP_BASE_CORE, n_lags)
    if name == "EXTENDED":
        base = (GROUP_BASE_CORE + GROUP_STRUCTURE + GROUP_AGGRESSION_EXTRA
                + GROUP_VOLUME + GROUP_CONTEXT + GROUP_TIME_EXTRA)
        return base + lag_names(GROUP_BASE_CORE, n_lags)
    if name == "PREVCMP":
        return prev_comparison_names()
    if name == "EXTENDED+PREVCMP":
        return (feature_set("EXTENDED", n_lags) + prev_comparison_names())
    if name == "STRUCTURE_ONLY":
        return GROUP_STRUCTURE + GROUP_CONTEXT
    if name == "AGG_ONLY":
        return (["AggBuyNorm", "AggSellNorm", "AggBalanceNorm", "AggTotalNorm"]
                + GROUP_AGGRESSION_EXTRA
                + lag_names(["AggBuyNorm", "AggSellNorm", "AggBalanceNorm",
                             "AggTotalNorm"], n_lags))
    if name == "VOL_ONLY":
        return (["QuantityNorm", "TradesNorm"] + GROUP_VOLUME
                + lag_names(["QuantityNorm", "TradesNorm"], n_lags))
    if name == "TIME_ONLY":
        return (["DurationResidual"] + GROUP_TIME_EXTRA
                + lag_names(["DurationResidual"], n_lags))
    raise ValueError(f"conjunto de features desconhecido: {name}")


ALL_ENGINEERED = (
    GROUP_BASE_CORE + GROUP_STRUCTURE + GROUP_AGGRESSION_EXTRA
    + GROUP_VOLUME + GROUP_CONTEXT + GROUP_TIME_EXTRA
)
