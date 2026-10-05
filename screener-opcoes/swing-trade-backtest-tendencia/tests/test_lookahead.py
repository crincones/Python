"""Nenhuma decisão pode mudar quando o futuro é removido (CLAUDE.md, seção 36)."""

from __future__ import annotations

import pandas as pd
import pytest

from mtf.models import MarketData
from mtf.signals.setups import align_to_h1, build_features, build_setups


def _truncate(data: MarketData, cutoff: pd.Timestamp) -> MarketData:
    """Mantém só as barras já fechadas em `cutoff` (como se o download fosse nesse instante)."""
    return MarketData(
        symbol=data.symbol,
        d1=data.d1[data.d1["close_time"] <= cutoff].reset_index(drop=True),
        h4=data.h4[data.h4["close_time"] <= cutoff].reset_index(drop=True),
        h1=data.h1[data.h1["close_time"] <= cutoff].reset_index(drop=True),
    )


@pytest.mark.parametrize("bar", [1500, 2000, 2345])
def test_features_do_not_change_when_future_is_removed(market, settings, bar):
    full = build_features(market, settings)
    cutoff = market.h1["close_time"].iloc[bar]
    partial = build_features(_truncate(market, cutoff), settings)
    assert len(partial) == bar + 1
    pd.testing.assert_frame_equal(partial, full.iloc[: bar + 1], check_exact=False, rtol=1e-12)


@pytest.mark.parametrize("name", ["A_retracao", "T_tendencia", "E_dist_0.30", "F_toque_mm21"])
def test_setups_do_not_change_when_future_is_removed(market, settings, name):
    variant = settings.variant(name)
    full = build_setups(build_features(market, settings), variant, settings, "TEST3")
    assert len(full) > 1
    bar = int(full["bar"].iloc[len(full) // 2])  # corta no meio dos setups da variante
    cutoff = market.h1["close_time"].iloc[bar]
    partial_features = build_features(_truncate(market, cutoff), settings)
    partial = build_setups(partial_features, variant, settings, "TEST3")
    expected = full[full["bar"] <= bar].reset_index(drop=True)
    pd.testing.assert_frame_equal(partial, expected, check_exact=False, rtol=1e-12)


def test_d1_value_during_session_is_previous_day(market):
    h1 = market.h1
    d1 = market.d1.assign(value=range(len(market.d1)))
    aligned = align_to_h1(h1, d1, ["value"])
    days = h1["time"].dt.normalize()
    assert aligned.loc[(days == days.iloc[0]).to_numpy(), "value"].isna().all()
    # Qualquer barra do 2º pregão enxerga só o D1 do 1º pregão.
    second = (days == days.unique()[1]).to_numpy()
    assert (aligned.loc[second, "value"] == 0).all()


def test_h4_bar_is_used_only_after_it_closes(market):
    h1, h4 = market.h1, market.h4.assign(value=range(len(market.h4)))
    aligned = align_to_h1(h1, h4, ["value"])
    days = h1["time"].dt.normalize()
    day2 = (days == days.unique()[1]).to_numpy()
    hours = h1.loc[day2, "time"].dt.hour.to_numpy()
    values = aligned.loc[day2, "value"].to_numpy()
    # H4 do dia 2: 08:00 (10–11h, fecha 12:00), 12:00 (fecha 16:00), 16:00 (fecha 20:00).
    first_h4_day2 = 3
    assert values[hours == 10][0] == first_h4_day2 - 1  # ainda o H4 16:00 do dia anterior
    assert values[hours == 11][0] == first_h4_day2  # H1 11:00 fecha 12:00
    assert values[hours == 14][0] == first_h4_day2
    assert values[hours == 15][0] == first_h4_day2 + 1  # H1 15:00 fecha 16:00
