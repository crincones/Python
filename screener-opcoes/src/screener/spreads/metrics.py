"""Métricas das travas de débito. Fórmulas conforme "Definições de métricas" do CLAUDE.md."""

from __future__ import annotations

import numpy as np
import pandas as pd

from screener.pricing.black_scholes import prob_above
from screener.spreads.builder import BULL_CALL

INVALID_NON_POSITIVE_DEBIT = "débito realista ≤ 0 (book inconsistente)"
INVALID_DEBIT_AT_LEAST_WIDTH = "débito realista ≥ largura (sem ganho possível)"
INVALID_NO_ATM_IV = "sem IV ATM do vencimento"


def spread_metrics(pairs: pd.DataFrame, atm: pd.DataFrame, lot_size: int) -> pd.DataFrame:
    """Acrescenta as métricas e a coluna `invalid_reason` (nulo = trava válida).

    `atm`: saída de pricing.implied_vol.atm_implied_vol.
    Convenções: spot = underlying_price da perna comprada; distâncias positivas = movimento
    necessário a favor da direção da trava; POP neutro ao risco (lognormal, drift r, IV ATM).
    """
    frame = pairs.merge(
        atm[["underlying", "expiration_date", "atm_iv"]],
        how="left",
        on=["underlying", "expiration_date"],
    )
    bull = (frame["strategy"] == BULL_CALL).to_numpy()
    spot = frame["long_underlying_price"]
    frame["spot"] = spot

    frame["width"] = (frame["short_strike"] - frame["long_strike"]).abs()
    frame["debit"] = frame["long_ask"] - frame["short_bid"]
    frame["debit_mid"] = frame["long_mid"] - frame["short_mid"]
    frame["execution_cost"] = frame["debit"] - frame["debit_mid"]
    frame["execution_cost_pct_width"] = (
        frame["execution_cost"] / (frame["short_strike"] - frame["long_strike"]).abs()
    )
    frame["max_gain"] = frame["width"] - frame["debit"]
    frame["max_loss"] = frame["debit"]
    frame["reward_risk"] = frame["max_gain"] / frame["debit"]
    frame["debit_to_width"] = frame["debit"] / frame["width"]
    frame["breakeven"] = np.where(
        bull, frame["long_strike"] + frame["debit"], frame["long_strike"] - frame["debit"]
    )

    move = np.where(bull, frame["breakeven"] - spot, spot - frame["breakeven"])
    frame["breakeven_distance_pct"] = move / spot
    one_sigma_move = frame["atm_iv"] * np.sqrt(frame["t_years"]) * spot
    frame["breakeven_distance_sigma"] = move / one_sigma_move

    above = prob_above(spot, frame["breakeven"], frame["t_years"], frame["rate"], frame["atm_iv"])
    frame["pop"] = np.where(bull, above, 1.0 - above)

    frame["debit_per_lot"] = frame["debit"] * lot_size
    frame["debit_mid_per_lot"] = frame["debit_mid"] * lot_size
    frame["max_gain_per_lot"] = frame["max_gain"] * lot_size
    frame["max_loss_per_lot"] = frame["max_loss"] * lot_size

    # A trava herda a pior liquidez entre as pernas.
    frame["liquidity_score"] = frame[["long_liquidity_score", "short_liquidity_score"]].min(axis=1)
    frame["worst_spread_pct_mid"] = frame[["long_spread_pct_mid", "short_spread_pct_mid"]].max(
        axis=1
    )
    frame["min_turnover_brl"] = frame[["long_turnover_brl", "short_turnover_brl"]].min(axis=1)
    frame["min_deals"] = frame[["long_deals", "short_deals"]].min(axis=1)

    reason = pd.Series(pd.NA, index=frame.index, dtype="string")
    reason = reason.mask(frame["debit"] <= 0, INVALID_NON_POSITIVE_DEBIT)
    reason = reason.mask(
        reason.isna() & (frame["debit"] >= frame["width"]), INVALID_DEBIT_AT_LEAST_WIDTH
    )
    reason = reason.mask(reason.isna() & frame["atm_iv"].isna(), INVALID_NO_ATM_IV)
    frame["invalid_reason"] = reason
    return frame
