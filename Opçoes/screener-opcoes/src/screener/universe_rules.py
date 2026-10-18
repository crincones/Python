"""Regras puras de seleção do universo: filtro do ativo-objeto e pré-filtro de séries da coleta."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from screener.calendar_b3 import B3Calendar
from screener.settings import CollectorSettings, SpreadSettings, UnderlyingFilterSettings

REJECT_EXCLUDED = "excluído na configuração"
REJECT_FEW_SERIES = "poucas séries listadas"
REJECT_NO_PRICE = "sem cotação do ativo-objeto"
REJECT_NO_HISTORY = "sem histórico D1"
REJECT_LOW_TURNOVER = "volume financeiro médio abaixo do mínimo"
REJECT_OUT_OF_TOP = "fora dos N mais líquidos"


def average_daily_turnover(rates: pd.DataFrame, expected_sessions: list[dt.date]) -> dict:
    """Volume financeiro médio diário (real_volume × close) nos pregões esperados.

    `rates` é o retorno de copy_rates (colunas time, close, real_volume). Barras fora dos
    pregões esperados (ex.: a barra parcial do dia) são ignoradas.
    """
    if rates.empty:
        return {
            "avg_daily_turnover_brl": np.nan,
            "sessions_used": 0,
            "missing_sessions": sorted(set(expected_sessions)),
        }
    bar_days = pd.to_datetime(rates["time"], unit="s").dt.date
    expected = set(expected_sessions)
    in_window = rates[bar_days.isin(expected)]
    turnover = in_window["real_volume"] * in_window["close"]
    present = set(bar_days[bar_days.isin(expected)])
    return {
        "avg_daily_turnover_brl": float(turnover.mean()) if len(turnover) else np.nan,
        "sessions_used": len(in_window),
        "missing_sessions": sorted(expected - present),
    }


def filter_underlyings(stats: pd.DataFrame, rules: UnderlyingFilterSettings) -> pd.DataFrame:
    """Aplica o filtro inicial do ativo-objeto.

    Entrada: underlying, listed_series, price, avg_daily_turnover_brl.
    Saída: mesmas colunas + passed_filter, reject_reason, liquidity_rank (1 = mais líquido).
    """
    result = stats.copy()
    reason = pd.Series(pd.NA, index=result.index, dtype="string")
    reason = reason.mask(result["underlying"].isin(rules.excluded_underlyings), REJECT_EXCLUDED)
    reason = reason.mask(
        reason.isna() & (result["listed_series"] < rules.min_listed_series), REJECT_FEW_SERIES
    )
    reason = reason.mask(reason.isna() & result["price"].isna(), REJECT_NO_PRICE)
    reason = reason.mask(reason.isna() & result["avg_daily_turnover_brl"].isna(), REJECT_NO_HISTORY)
    reason = reason.mask(
        reason.isna() & (result["avg_daily_turnover_brl"] < rules.min_avg_daily_turnover_brl),
        REJECT_LOW_TURNOVER,
    )

    eligible = reason.isna()
    rank = result.loc[eligible, "avg_daily_turnover_brl"].rank(ascending=False, method="first")
    result["liquidity_rank"] = rank.astype("Int64")
    out_of_top = (result["liquidity_rank"] > rules.max_underlyings).fillna(False)
    reason = reason.mask(eligible & out_of_top, REJECT_OUT_OF_TOP)

    result["reject_reason"] = reason
    result["passed_filter"] = reason.isna()
    return result.sort_values(
        ["passed_filter", "avg_daily_turnover_brl"], ascending=[False, False]
    ).reset_index(drop=True)


def select_candidate_series(
    options: pd.DataFrame,
    spots: pd.Series,
    snapshot_date: dt.date,
    calendar: B3Calendar,
    collector: CollectorSettings,
    spreads: SpreadSettings,
) -> pd.DataFrame:
    """Pré-filtro da coleta: janela de DTE (dias úteis) e faixa de strike em torno do spot.

    `options` precisa de underlying, strike e expiration_date; `spots` é indexado por ativo.
    """
    frame = options.copy()
    frame["dte_business_days"] = calendar.sessions_until(snapshot_date, frame["expiration_date"])
    spot = frame["underlying"].map(spots)
    in_dte = frame["dte_business_days"].between(
        spreads.dte_min_business_days, spreads.dte_max_business_days
    )
    in_strike = (frame["strike"] / spot - 1).abs() <= collector.strike_range_pct_spot
    return frame[in_dte & in_strike.fillna(False)].reset_index(drop=True)


def feed_problem(raw: pd.DataFrame, min_quoted_fraction: float) -> str | None:
    """Detecta feed parado nos registros brutos de um ativo (symbol_info + underlying_*).

    Retorna a descrição do problema ou None se a leitura parece saudável.
    """
    if raw.empty:
        return "nenhuma série lida"
    underlying_quoted = (raw[["underlying_bid", "underlying_ask", "underlying_last"]] > 0).any(
        axis=1
    )
    if not underlying_quoted.all():
        return "ativo-objeto sem cotação durante a leitura"
    quoted_fraction = float((raw["time"] > 0).mean())
    if quoted_fraction < min_quoted_fraction:
        return f"só {quoted_fraction:.1%} das séries com tick (mínimo {min_quoted_fraction:.1%})"
    return None
