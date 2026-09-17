"""Liquidez própria de cada série: filtros mínimos e score dentro do ativo-objeto."""

from __future__ import annotations

import pandas as pd

from screener.settings import SeriesLiquiditySettings

REJECT_NO_BOOK = "sem book (bid ou ask ausente)"
REJECT_STALE = "cotação velha"
REJECT_LOW_PREMIUM = "prêmio abaixo do mínimo"
REJECT_WIDE_SPREAD = "spread bid/ask largo"
REJECT_LOW_TURNOVER = "volume financeiro baixo"
REJECT_FEW_DEALS = "poucos negócios"
REJECT_LOW_OPEN_INTEREST = "open interest baixo ou ausente"

# Componente do score → (coluna, maior é melhor)
SCORE_COMPONENTS: dict[str, tuple[str, bool]] = {
    "spread": ("spread_pct_mid", False),
    "turnover": ("turnover_brl", True),
    "deals": ("deals", True),
    "open_interest": ("open_interest", True),
}


def _reject_reasons(options: pd.DataFrame, rules: SeriesLiquiditySettings) -> pd.Series:
    checks: list[tuple[pd.Series, str]] = [
        (options["bid"].isna() | options["ask"].isna(), REJECT_NO_BOOK),
        (~(options["quote_age_seconds"] <= rules.max_quote_age_seconds), REJECT_STALE),
        (options["mid"] < rules.min_mid_price_brl, REJECT_LOW_PREMIUM),
        (options["spread_pct_mid"] > rules.max_spread_pct_mid, REJECT_WIDE_SPREAD),
        (options["turnover_brl"] < rules.min_turnover_brl, REJECT_LOW_TURNOVER),
        (options["deals"] < rules.min_deals, REJECT_FEW_DEALS),
    ]
    if rules.min_open_interest is not None:
        low_oi = ~(options["open_interest"] >= rules.min_open_interest)
        checks.append((low_oi, REJECT_LOW_OPEN_INTEREST))

    reason = pd.Series(pd.NA, index=options.index, dtype="string")
    for failed, label in checks:
        reason = reason.mask(reason.isna() & failed.fillna(True), label)
    return reason


def active_weights(options: pd.DataFrame, rules: SeriesLiquiditySettings) -> dict[str, float]:
    """Pesos normalizados. OI só conta se houver filtro de OI configurado e dado disponível."""
    weights = rules.weights.model_dump()
    if rules.min_open_interest is None or options["open_interest"].isna().all():
        weights.pop("open_interest")
    total = sum(weights.values())
    return {name: value / total for name, value in weights.items()}


def evaluate_series_liquidity(
    options: pd.DataFrame, rules: SeriesLiquiditySettings
) -> pd.DataFrame:
    """Colunas novas, mesmo índice:

    - liquidity_ok, liquidity_reject_reason
    - liquidity_score ∈ [0, 1]: média ponderada dos percentis de cada componente entre as séries
      aprovadas do mesmo ativo-objeto (1 = mais líquida do ativo). NaN se reprovada.
    """
    reason = _reject_reasons(options, rules)
    ok = reason.isna()
    weights = active_weights(options, rules)

    score = pd.Series(0.0, index=options.index)
    approved = options[ok]
    for name, weight in weights.items():
        column, higher_is_better = SCORE_COMPONENTS[name]
        pct = approved.groupby("underlying")[column].rank(
            pct=True, ascending=higher_is_better, method="average"
        )
        score.loc[approved.index] += weight * pct
    return pd.DataFrame(
        {
            "liquidity_ok": ok,
            "liquidity_reject_reason": reason,
            "liquidity_score": score.where(ok),
        },
        index=options.index,
    )
