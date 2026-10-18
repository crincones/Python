"""Qualidade de cotação e liquidez de cada série (perna). Funções puras sobre a cadeia.

Cada série recebe `quote_flags` (lista de problemas, vazia = aprovada) e `liquidity_score` ∈ [0, 1]
(média ponderada de percentis entre as séries aprovadas da mesma cadeia: spread menor, volume
financeiro maior, mais negócios). Open interest não entra: a XP não o fornece via MT5.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

FLAG_NO_BOOK = "sem bid/ask válido"
FLAG_STALE = "cotação antiga"
FLAG_NO_TICK = "sem tick"
FLAG_LOW_PREMIUM = "prêmio muito baixo"
FLAG_WIDE_SPREAD = "spread largo"
FLAG_LOW_TURNOVER = "volume financeiro baixo"
FLAG_FEW_DEALS = "poucos negócios"

SCORE_WEIGHTS = {
    "spread_pct_mid": (0.40, False),
    "turnover_brl": (0.35, True),
    "deals": (0.25, True),
}


@dataclass(frozen=True, slots=True)
class LiquidityRules:
    max_spread_pct_mid: float
    min_mid_price_brl: float
    min_turnover_brl: float
    min_deals: int
    max_quote_age_seconds: float


def quote_flags(chain: pd.DataFrame, rules: LiquidityRules) -> pd.Series:
    """Lista de problemas por série. Cotações antigas ou inválidas nunca passam como atuais."""
    checks: list[tuple[pd.Series, str]] = [
        (chain["quote_time"].isna(), FLAG_NO_TICK),
        (chain["mid"].isna(), FLAG_NO_BOOK),
        (~(chain["quote_age_seconds"] <= rules.max_quote_age_seconds), FLAG_STALE),
        (chain["mid"] < rules.min_mid_price_brl, FLAG_LOW_PREMIUM),
        (chain["spread_pct_mid"] > rules.max_spread_pct_mid, FLAG_WIDE_SPREAD),
        (chain["turnover_brl"].fillna(0) < rules.min_turnover_brl, FLAG_LOW_TURNOVER),
        (chain["deals"].fillna(0) < rules.min_deals, FLAG_FEW_DEALS),
    ]
    flags: list[list[str]] = [[] for _ in range(len(chain))]
    for failed, label in checks:
        for i, bad in enumerate(failed.fillna(False).to_numpy()):
            if bad and (label != FLAG_STALE or FLAG_NO_TICK not in flags[i]):
                flags[i].append(label)
    return pd.Series(flags, index=chain.index, dtype=object)


def evaluate_liquidity(chain: pd.DataFrame, rules: LiquidityRules) -> pd.DataFrame:
    flags = quote_flags(chain, rules)
    ok = flags.map(len) == 0
    score = pd.Series(0.0, index=chain.index)
    approved = chain[ok]
    for column, (weight, higher_is_better) in SCORE_WEIGHTS.items():
        pct = approved[column].rank(pct=True, ascending=higher_is_better, method="average")
        score.loc[approved.index] += weight * pct
    # Reprovadas: score calculado sobre a cadeia toda e reduzido, só para ordenar entre si.
    rejected = chain[~ok]
    if len(rejected):
        partial = pd.Series(0.0, index=rejected.index)
        for column, (weight, higher_is_better) in SCORE_WEIGHTS.items():
            pct = chain[column].rank(pct=True, ascending=higher_is_better, method="average")
            partial += weight * pct.loc[rejected.index].fillna(0)
        score.loc[rejected.index] = 0.5 * partial
    return pd.DataFrame(
        {"quote_flags": flags, "liquidity_ok": ok, "liquidity_score": score}, index=chain.index
    )
