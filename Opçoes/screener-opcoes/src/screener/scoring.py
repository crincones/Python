"""Score final das travas e ranking alinhado ao viés.

1. Perfil: só travas com POP em [pop_min, pop_max] recebem score.
2. Score 0–100 = soma ponderada dos percentis (por estratégia, entre as travas da faixa) de:
   custo de execução em % da largura (menor é melhor), liquidez (maior) e R/R (maior).
3. Ranking: trava na faixa E direção igual ao viés final do ativo (alta → bull_call,
   baixa → bear_put). Posição 1 = maior score dentro da estratégia.
"""

from __future__ import annotations

import pandas as pd

from screener.settings import ScoringSettings

SCORE_SCALE = 100

# componente do YAML → (coluna da trava, maior é melhor)
SCORE_COMPONENTS: dict[str, tuple[str, bool]] = {
    "execution_cost": ("execution_cost_pct_width", False),
    "liquidity": ("liquidity_score", True),
    "reward_risk": ("reward_risk", True),
}


def score_spreads(
    spreads: pd.DataFrame, bias: pd.DataFrame, settings: ScoringSettings
) -> pd.DataFrame:
    """Colunas novas (mesmo índice): in_pop_band, pct_<componente>, score, bias, bias_source,
    bias_match, ranked, rank."""
    in_band = spreads["pop"].between(settings.pop_min, settings.pop_max)
    pool = spreads[in_band]
    weights = settings.weights.model_dump()

    result = pd.DataFrame({"in_pop_band": in_band}, index=spreads.index)
    score = pd.Series(0.0, index=pool.index)
    for name, (column, higher_is_better) in SCORE_COMPONENTS.items():
        pct = pool.groupby("strategy")[column].rank(
            pct=True, ascending=higher_is_better, method="average"
        )
        result[f"pct_{name}"] = pct
        score += weights[name] * pct
    result["score"] = (score * SCORE_SCALE).reindex(spreads.index)

    by_underlying = bias.set_index("underlying")
    result["bias"] = spreads["underlying"].map(by_underlying["bias"]).fillna("neutro")
    result["bias_source"] = spreads["underlying"].map(by_underlying["bias_source"])
    result["bias_match"] = spreads["direction"] == result["bias"]
    result["ranked"] = in_band & result["bias_match"]

    ranked = result[result["ranked"]].assign(strategy=spreads["strategy"])
    result["rank"] = (
        ranked.groupby("strategy")["score"].rank(ascending=False, method="first").astype("Int64")
    )
    result["rank"] = result["rank"].astype("Int64")
    return result
