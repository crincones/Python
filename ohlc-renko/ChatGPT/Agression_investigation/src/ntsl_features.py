"""
Subconjunto de features REPRODUZIVEL EM NTSL.

Restricao verificada (secao 29 do CLAUDE.md — nao inventar sintaxe):
foram levantadas as funcoes NTSL efetivamente usadas nos indicadores ja
compilados do usuario em ``ProfitChart/Indicadores``:

    AgressionVolBuy   AgressionVolSell   AgressionVolBalance
    QuantityVol(false, false)            BarDurationF()
    Open High Low Close   Date   CurrentBar   MinPriceIncrement()
    Abs  Sqrt  Round  Power  Media  MediaExp  Summation  Highest  Lowest
    PlotText  Plot  PaintBar  SetPlotColor  RGB

NAO existe, entre as funcoes verificadas, nenhuma que devolva o NUMERO DE
NEGOCIOS da barra (a coluna ``Trades`` do CSV). Portanto toda feature
derivada de ``Trades`` fica FORA do modelo exportavel:

    TradesNorm, TradesResidual20, TradesRatio20, QuantityPerTrade,
    TradesPerQuantity, AggTotalPerTrade, QuantityPerTradeRatio20

Elas continuam sendo estudadas na pesquisa (a pergunta cientifica da
secao 40 inclui "numero de negocios"), mas o modelo que vira indicador so
pode usar o que o NTSL consegue calcular.
"""
from __future__ import annotations

# Features contemporaneas calculaveis em NTSL
NTSL_CONTEMPORANEOUS = [
    "AggBuyNorm",        # AgressionVolBuy / (High-Low)
    "AggSellNorm",       # AgressionVolSell / (High-Low)
    "AggBalanceNorm",    # (Buy-Sell) / (High-Low)
    "AggTotalNorm",      # (Buy+Sell) / (High-Low)
    "QuantityNorm",      # QuantityVol(false,false) / (High-Low)
    "DurationResidual",  # BarDurationF - Media(20, BarDurationF)
    "Range",             # High - Low
    "BodyNorm",          # |Close-Open| / (High-Low)
    "Direction",         # sinal de Close-Open
    "RunLength",         # barras consecutivas na mesma direcao ate t
    "AggImbalance",      # (Buy-Sell) / (Buy+Sell)
    "AggBalanceChange",  # AggBalanceNorm[0] - AggBalanceNorm[1]
    "RangeRatio20",      # Range / Media(20, Range)
    "AggTotalRatio20",   # AggTotal / Media(20, AggTotal)
    "QuantityRatio20",   # Quantity / Media(20, Quantity)
]

# Features cujo lag tambem e trivial em NTSL (basta indexar a serie)
NTSL_LAGGABLE = [
    "AggBuyNorm", "AggSellNorm", "AggBalanceNorm", "AggTotalNorm",
    "QuantityNorm", "DurationResidual",
]

EXCLUDED_NEEDS_TRADES = [
    "TradesNorm", "TradesResidual20", "TradesRatio20", "QuantityPerTrade",
    "TradesPerQuantity", "AggTotalPerTrade", "QuantityPerTradeRatio20",
    "AggTotalPerQuantity", "AggShareOfQuantity",
]


def ntsl_feature_set(n_lags: int = 3) -> list[str]:
    cols = list(NTSL_CONTEMPORANEOUS)
    for c in NTSL_LAGGABLE:
        cols += [f"{c}_lag{k}" for k in range(1, n_lags + 1)]
    return cols


# Como cada feature e obtida no NTSL. Usado para gerar o preambulo do
# indicador e para a auditoria Python <-> NTSL.
NTSL_EXPRESSIONS = {
    "AggBuyNorm":       "agrB[{lag}] / rngSafe[{lag}]",
    "AggSellNorm":      "agrS[{lag}] / rngSafe[{lag}]",
    "AggBalanceNorm":   "(agrB[{lag}] - agrS[{lag}]) / rngSafe[{lag}]",
    "AggTotalNorm":     "(agrB[{lag}] + agrS[{lag}]) / rngSafe[{lag}]",
    "QuantityNorm":     "qtd[{lag}] / rngSafe[{lag}]",
    "DurationResidual": "dur[{lag}] - mDur[{lag}]",
    "Range":            "rng[{lag}]",
    "BodyNorm":         "corpo[{lag}] / rngSafe[{lag}]",
    "Direction":        "dirn[{lag}]",
    "RunLength":        "runLen[{lag}]",
    "AggImbalance":     "imbal[{lag}]",
    "AggBalanceChange": "balNorm[{lag}] - balNorm[{lag}+1]",
    "RangeRatio20":     "rng[{lag}] / mRng[{lag}]",
    "AggTotalRatio20":  "totAgr[{lag}] / mTot[{lag}]",
    "QuantityRatio20":  "qtd[{lag}] / mQtd[{lag}]",
}
