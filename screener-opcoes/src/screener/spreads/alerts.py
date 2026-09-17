"""Alerta obrigatório de risco de exercício antecipado da perna vendida americana.

O alerta não remove a trava do ranking: só sinaliza (CLAUDE.md).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from screener.settings import EarlyExerciseAlertSettings

ALERT_LOW_EXTRINSIC = "vendida americana ITM com pouco valor extrínseco"
ALERT_DIVIDEND = "provento com data ex antes do vencimento (vendida americana)"
WINDOW_KEYS = ["underlying", "expiration_date"]


def early_exercise_alerts(
    spreads: pd.DataFrame,
    dividends: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    rules: EarlyExerciseAlertSettings,
) -> pd.DataFrame:
    """Colunas: short_intrinsic, short_extrinsic, early_exercise_alert, early_exercise_reason.

    - Extrínseco da vendida = mid − intrínseco (intrínseco com o spot da trava).
    - Pouco extrínseco: < min_extrinsic_pct_premium × mid OU < min_extrinsic_brl.
    - Provento: data ex em [data do snapshot, vencimento] para o ativo-objeto.
    Travas com vendida europeia nunca recebem alerta.
    """
    is_call = (spreads["option_type"] == "call").to_numpy()
    strike, spot, mid = spreads["short_strike"], spreads["spot"], spreads["short_mid"]
    intrinsic = pd.Series(np.where(is_call, spot - strike, strike - spot), index=spreads.index)
    intrinsic = intrinsic.clip(lower=0.0)
    extrinsic = mid - intrinsic
    american = spreads["short_exercise_style"] == "american"

    low_extrinsic = (intrinsic > 0) & (
        (extrinsic < rules.min_extrinsic_pct_premium * mid) | (extrinsic < rules.min_extrinsic_brl)
    )

    windows = spreads[WINDOW_KEYS].drop_duplicates().merge(dividends, on="underlying")
    start = pd.Timestamp(snapshot_date).tz_localize(None).normalize()
    flagged = windows[
        (windows["ex_date"] >= start) & (windows["ex_date"] <= windows["expiration_date"])
    ]
    has_dividend = pd.Series(
        pd.MultiIndex.from_frame(spreads[WINDOW_KEYS]).isin(
            pd.MultiIndex.from_frame(flagged[WINDOW_KEYS])
        ),
        index=spreads.index,
    )

    reasons = pd.Series(pd.NA, index=spreads.index, dtype="string")
    reasons = reasons.mask(american & low_extrinsic, ALERT_LOW_EXTRINSIC)
    both = american & low_extrinsic & has_dividend
    reasons = reasons.mask(american & has_dividend & ~low_extrinsic, ALERT_DIVIDEND)
    reasons = reasons.mask(both, f"{ALERT_LOW_EXTRINSIC}; {ALERT_DIVIDEND}")
    return pd.DataFrame(
        {
            "short_intrinsic": intrinsic,
            "short_extrinsic": extrinsic,
            "early_exercise_alert": reasons.notna(),
            "early_exercise_reason": reasons,
        },
        index=spreads.index,
    )
