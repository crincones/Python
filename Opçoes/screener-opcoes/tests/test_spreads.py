from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from screener.data.dividends import load_dividends
from screener.pricing import black_scholes as bs
from screener.pricing.implied_vol import atm_implied_vol
from screener.settings import load_settings
from screener.spreads import alerts, metrics
from screener.spreads.builder import BEAR_PUT, BULL_CALL, build_spread_pairs

SETTINGS = load_settings()
EXPIRY = pd.Timestamp("2026-10-16")
RATE = float(bs.continuous_rate(0.139))
T = 20 / 252


def _leg(symbol: str, option_type: str, strike: float, bid: float, ask: float, **kw) -> dict:
    row = {
        "snapshot_time": pd.Timestamp("2026-09-17 11:20:13", tz="America/Sao_Paulo"),
        "underlying": "PETR4",
        "expiration_date": EXPIRY,
        "option_type": option_type,
        "dte_business_days": 20,
        "t_years": T,
        "rate": RATE,
        "symbol": symbol,
        "strike": strike,
        "exercise_style": "european",
        "bid": bid,
        "ask": ask,
        "mid": (bid + ask) / 2,
        "iv": 0.44,
        "iv_status": "ok",
        "spread_pct_mid": (ask - bid) / ((bid + ask) / 2),
        "turnover_brl": 100_000.0,
        "deals": 50,
        "liquidity_ok": True,
        "liquidity_score": 0.5,
        "underlying_price": 48.29,
    }
    row.update(kw)
    return row


def _series() -> pd.DataFrame:
    return pd.DataFrame(
        [
            # Puts reais de PETR4 (17/09/2026)
            _leg("PETRV458", "put", 44.11, 0.68, 0.70, liquidity_score=0.315),
            _leg("PETRV512", "put", 43.11, 0.50, 0.52, liquidity_score=0.144),
            _leg("CALL48", "call", 48.0, 2.20, 2.24),
            _leg("CALL50", "call", 50.0, 1.30, 1.33, exercise_style="american"),
            _leg("CALL60", "call", 60.0, 0.10, 0.12),  # largura 12 > 10% do spot
            _leg("ILLIQ", "call", 49.0, 1.70, 1.90, liquidity_ok=False),
            _leg("NOIV", "call", 51.0, 0.90, 0.95, iv=np.nan, iv_status="nao_convergiu"),
        ]
    )


def test_builder_pairs_only_valid_debit_spreads() -> None:
    pairs = build_spread_pairs(_series(), max_width_pct_spot=0.10)
    found = set(zip(pairs["strategy"], pairs["long_symbol"], pairs["short_symbol"], strict=True))
    assert found == {(BEAR_PUT, "PETRV458", "PETRV512"), (BULL_CALL, "CALL48", "CALL50")}
    assert set(pairs["direction"]) == {"alta", "baixa"}


def test_metrics_match_hand_calculation_for_real_bear_put() -> None:
    pairs = build_spread_pairs(_series(), max_width_pct_spot=0.10)
    atm = pd.DataFrame({"underlying": ["PETR4"], "expiration_date": [EXPIRY], "atm_iv": [0.4387]})
    result = metrics.spread_metrics(pairs, atm, lot_size=100)
    row = result[result["strategy"] == BEAR_PUT].iloc[0]

    assert row["width"] == pytest.approx(1.00)
    assert row["debit"] == pytest.approx(0.70 - 0.50)
    assert row["debit_mid"] == pytest.approx(0.69 - 0.51)
    assert row["execution_cost"] == pytest.approx(0.20 - 0.18)
    assert row["execution_cost_pct_width"] == pytest.approx(0.02)
    assert row["max_gain"] == pytest.approx(0.80)
    assert row["reward_risk"] == pytest.approx(4.0)
    assert row["debit_to_width"] == pytest.approx(0.20)
    assert row["breakeven"] == pytest.approx(44.11 - 0.20)
    assert row["breakeven_distance_pct"] == pytest.approx((48.29 - 43.91) / 48.29)
    sigma_move = 0.4387 * np.sqrt(T) * 48.29
    assert row["breakeven_distance_sigma"] == pytest.approx((48.29 - 43.91) / sigma_move)
    expected_pop = 1 - float(bs.prob_above(48.29, 43.91, T, RATE, 0.4387))
    assert row["pop"] == pytest.approx(expected_pop)
    assert row["debit_per_lot"] == pytest.approx(20.0)
    assert row["max_gain_per_lot"] == pytest.approx(80.0)
    assert row["liquidity_score"] == pytest.approx(0.144)  # pior perna
    assert pd.isna(row["invalid_reason"])


def test_bull_call_breakeven_and_pop_direction() -> None:
    pairs = build_spread_pairs(_series(), max_width_pct_spot=0.10)
    atm = pd.DataFrame({"underlying": ["PETR4"], "expiration_date": [EXPIRY], "atm_iv": [0.44]})
    row = metrics.spread_metrics(pairs, atm, 100).query("strategy == @BULL_CALL").iloc[0]
    assert row["debit"] == pytest.approx(2.24 - 1.30)
    assert row["breakeven"] == pytest.approx(48.0 + 0.94)
    assert row["breakeven_distance_pct"] == pytest.approx((48.94 - 48.29) / 48.29)
    assert row["pop"] == pytest.approx(float(bs.prob_above(48.29, 48.94, T, RATE, 0.44)))


def test_invalid_reasons() -> None:
    pairs = build_spread_pairs(_series(), max_width_pct_spot=0.10)
    pairs.loc[pairs["strategy"] == BULL_CALL, "short_bid"] = 2.30  # débito negativo
    pairs.loc[pairs["strategy"] == BEAR_PUT, "short_bid"] = -0.40  # débito > largura
    result = metrics.spread_metrics(
        pairs, pd.DataFrame(columns=["underlying", "expiration_date", "atm_iv"]), 100
    )
    reasons = dict(zip(result["strategy"], result["invalid_reason"], strict=True))
    assert reasons[BULL_CALL] == metrics.INVALID_NON_POSITIVE_DEBIT
    assert reasons[BEAR_PUT] == metrics.INVALID_DEBIT_AT_LEAST_WIDTH

    no_atm = metrics.spread_metrics(
        build_spread_pairs(_series(), 0.10),
        pd.DataFrame(columns=["underlying", "expiration_date", "atm_iv"]),
        100,
    )
    assert (no_atm["invalid_reason"] == metrics.INVALID_NO_ATM_IV).all()


def test_atm_iv_ignores_broken_book_and_far_strikes() -> None:
    pricing = SETTINGS.pricing
    series = pd.DataFrame(
        [
            _leg("BROKEN", "put", 48.3, 0.04, 2.30, iv=0.146),
            _leg("GOOD_PUT", "put", 48.0, 1.60, 1.64, iv=0.23),
            _leg("GOOD_CALL", "call", 49.0, 1.20, 1.24, iv=0.22),
            _leg("FAR", "call", 40.0, 8.5, 8.6, iv=0.9, expiration_date=pd.Timestamp("2026-10-23")),
        ]
    )
    atm = atm_implied_vol(series, pricing).set_index("expiration_date")
    assert atm.loc[EXPIRY, "atm_iv"] == pytest.approx((0.23 + 0.22) / 2)
    assert pd.Timestamp("2026-10-23") not in atm.index


def _spreads_for_alerts() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "underlying": ["PETR4", "PETR4", "PETR4", "VALE3"],
            "expiration_date": [EXPIRY] * 4,
            "option_type": ["call", "call", "call", "call"],
            "short_strike": [40.0, 40.0, 55.0, 70.0],
            "short_mid": [8.30, 8.30, 0.40, 1.00],
            "spot": [48.29, 48.29, 48.29, 73.0],
            "short_exercise_style": ["american", "european", "american", "american"],
        }
    )


def test_early_exercise_alert_rules() -> None:
    rules = SETTINGS.early_exercise_alert
    no_dividends = pd.DataFrame(columns=["underlying", "ex_date", "description"])
    snap = pd.Timestamp("2026-09-17 11:20", tz="America/Sao_Paulo")
    result = alerts.early_exercise_alerts(_spreads_for_alerts(), no_dividends, snap, rules)
    # ITM americana, extrínseco 8,30 − 8,29 = 0,01 < R$ 0,02 → alerta
    assert result.loc[0, "early_exercise_reason"] == alerts.ALERT_LOW_EXTRINSIC
    assert result.loc[0, "short_extrinsic"] == pytest.approx(0.01)
    assert not result.loc[1, "early_exercise_alert"]  # europeia nunca
    assert not result.loc[2, "early_exercise_alert"]  # OTM
    # VALE3: ITM, extrínseco 1,00 − 3,00 < 0 → alerta
    assert result.loc[3, "early_exercise_alert"]


def test_early_exercise_alert_for_dividend_in_window(tmp_path) -> None:
    csv = tmp_path / "proventos.csv"
    csv.write_text(
        "underlying,ex_date,description\npetr4,2026-10-01,JCP\nVALE3,2026-12-01,depois\n",
        encoding="utf-8",
    )
    dividends = load_dividends(csv)
    snap = pd.Timestamp("2026-09-17 11:20", tz="America/Sao_Paulo")
    rules = SETTINGS.early_exercise_alert
    result = alerts.early_exercise_alerts(_spreads_for_alerts(), dividends, snap, rules)
    assert alerts.ALERT_DIVIDEND in result.loc[0, "early_exercise_reason"]
    assert alerts.ALERT_LOW_EXTRINSIC in result.loc[0, "early_exercise_reason"]
    assert not result.loc[1, "early_exercise_alert"]  # europeia, mesmo com provento
    assert result.loc[2, "early_exercise_reason"] == alerts.ALERT_DIVIDEND  # OTM mas com provento
    assert (
        result.loc[3, "early_exercise_reason"] == alerts.ALERT_LOW_EXTRINSIC
    )  # ex após vencimento


def test_dividends_file_requires_columns(tmp_path) -> None:
    csv = tmp_path / "proventos.csv"
    csv.write_text("ativo,data\nPETR4,2026-10-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas ausentes"):
        load_dividends(csv)


def test_versioned_dividends_file_loads() -> None:
    frame = load_dividends(SETTINGS.paths.dividends_file)
    assert list(frame.columns) == ["underlying", "ex_date", "description"]
