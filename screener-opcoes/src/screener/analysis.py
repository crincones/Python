"""Etapa de análise: IV, liquidez, travas, alertas, viés e score. Sem MT5."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from screener.data.schema import (
    BIAS_COLUMNS,
    BIAS_TIMEFRAME_FIELDS,
    OPTIONS_COLUMNS,
    SCORE_COLUMNS,
    SERIES_EXTRA_COLUMNS,
    SPREADS_COLUMNS,
)
from screener.liquidity import active_weights, evaluate_series_liquidity
from screener.pricing.implied_vol import atm_implied_vol, options_implied_vol
from screener.scoring import score_spreads
from screener.settings import Settings
from screener.signals.direction import automatic_bias, resolve_bias
from screener.spreads.alerts import early_exercise_alerts
from screener.spreads.builder import build_spread_pairs
from screener.spreads.metrics import spread_metrics

log = logging.getLogger(__name__)

SPREAD_SORT = ["underlying", "strategy", "expiration_date", "long_strike", "short_strike"]


@dataclass(frozen=True)
class AnalysisResult:
    series: pd.DataFrame
    spreads: pd.DataFrame
    bias: pd.DataFrame
    summary: dict[str, Any]


def bias_columns(settings: Settings) -> list[str]:
    per_timeframe = [
        f"{tf}_{field}" for tf in settings.signals.timeframes for field in BIAS_TIMEFRAME_FIELDS
    ]
    return list(BIAS_COLUMNS) + per_timeframe


def analyze(
    options: pd.DataFrame, dividends: pd.DataFrame, bars: pd.DataFrame, settings: Settings
) -> AnalysisResult:
    rate_annual = settings.market.risk_free_rate_annual
    iv = options_implied_vol(options, rate_annual, settings.pricing)
    liquidity = evaluate_series_liquidity(options, settings.series_liquidity)
    series = options.join(iv).join(liquidity)[list(OPTIONS_COLUMNS) + list(SERIES_EXTRA_COLUMNS)]

    atm = atm_implied_vol(series, settings.pricing)
    pairs = build_spread_pairs(series, settings.spreads.max_width_pct_spot)
    with_metrics = spread_metrics(pairs, atm, settings.spreads.lot_size)
    invalid_counts = with_metrics["invalid_reason"].value_counts().to_dict()
    valid = with_metrics[with_metrics["invalid_reason"].isna()].reset_index(drop=True)

    snapshot_time = options["snapshot_time"].iloc[0] if len(options) else pd.NaT
    alerts = early_exercise_alerts(valid, dividends, snapshot_time, settings.early_exercise_alert)
    metric_columns = [c for c in SPREADS_COLUMNS if c not in SCORE_COLUMNS]
    spreads = valid.join(alerts)[metric_columns]

    if bars.empty:
        log.warning("Snapshot sem barras D1/H4: viés automático indisponível")
    auto = automatic_bias(bars, settings.signals) if not bars.empty else pd.DataFrame()
    bias = resolve_bias(
        options["underlying"].unique().tolist(), auto, settings.bias, settings.signals
    ).reindex(columns=bias_columns(settings))
    scores = score_spreads(spreads, bias, settings.scoring)
    spreads = (
        spreads.join(scores)[list(SPREADS_COLUMNS)].sort_values(SPREAD_SORT).reset_index(drop=True)
    )

    summary = {
        "risk_free_rate_annual": rate_annual,
        "series_total": len(series),
        "series_iv_status": series["iv_status"].value_counts().to_dict(),
        "series_liquidity_rejections": series["liquidity_reject_reason"].value_counts().to_dict(),
        "series_eligible": int((series["liquidity_ok"] & series["iv"].notna()).sum()),
        "liquidity_weights_used": active_weights(options, settings.series_liquidity),
        "pairs_built": len(pairs),
        "pairs_invalid": invalid_counts,
        "spreads_valid": len(spreads),
        "spreads_by_strategy": spreads["strategy"].value_counts().to_dict(),
        "spreads_with_early_exercise_alert": int(spreads["early_exercise_alert"].sum()),
        "dividends_loaded": len(dividends),
        "bias": dict(zip(bias["underlying"], bias["bias"], strict=True)),
        "bias_source": bias["bias_source"].value_counts().to_dict(),
        "spreads_in_pop_band": int(spreads["in_pop_band"].sum()),
        "spreads_ranked": spreads[spreads["ranked"]]["strategy"].value_counts().to_dict(),
    }
    log.info(
        "Análise: %d séries, %d elegíveis, %d pares, %d travas válidas (%d com alerta)",
        summary["series_total"],
        summary["series_eligible"],
        summary["pairs_built"],
        summary["spreads_valid"],
        summary["spreads_with_early_exercise_alert"],
    )
    log.info(
        "Score: %d travas na faixa de POP, ranqueadas por estratégia: %s",
        summary["spreads_in_pop_band"],
        summary["spreads_ranked"],
    )
    return AnalysisResult(series=series, spreads=spreads, bias=bias, summary=summary)
