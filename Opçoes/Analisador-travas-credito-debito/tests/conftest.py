"""Cadeia sintética para testes (preços Black-Scholes). Nunca usada fora dos testes."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from travas.calendar_b3 import B3Calendar
from travas.data.normalize import CHAIN_COLUMNS
from travas.options import pricing
from travas.options.analysis import AnalysisParams
from travas.options.liquidity import LiquidityRules
from travas.options.models import Direction, Flow
from travas.settings import load_settings

SETTINGS = load_settings()
TODAY = dt.date(2026, 10, 14)
SPOT = 31.0
SIGMA = 0.35
RATE_ANNUAL = 0.14


@pytest.fixture(scope="session")
def calendar() -> B3Calendar:
    return B3Calendar.from_csv(SETTINGS.paths.holidays_file)


def synthetic_chain(calendar: B3Calendar, half_spread: float = 0.02) -> pd.DataFrame:
    rows = []
    expirations = [dt.date(2026, 11, 13), dt.date(2026, 12, 18)]
    r = float(pricing.continuous_rate(RATE_ANNUAL))
    now = pd.Timestamp("2026-10-14 11:00", tz="America/Sao_Paulo")
    for exp in expirations:
        dte = int(calendar.sessions_until(TODAY, pd.Series([exp])).iloc[0])
        t = dte / 252
        for strike in np.arange(26.0, 37.0, 1.0):
            for kind in ("call", "put"):
                theo = float(pricing.price(SPOT, strike, t, r, SIGMA, kind == "call"))
                bid = round(max(theo * (1 - half_spread), 0.01), 2)
                ask = round(theo * (1 + half_spread) + 0.01, 2)
                rows.append(
                    {
                        "symbol": f"TEST{'C' if kind == 'call' else 'P'}{exp:%m}{int(strike)}",
                        "underlying": "TEST3",
                        "option_type": kind,
                        "exercise_style": "american" if kind == "call" else "european",
                        "strike": strike,
                        "expiration_date": exp,
                        "dte_business_days": dte,
                        "dte_calendar_days": (exp - TODAY).days,
                        "bid": bid,
                        "ask": ask,
                        "last": round(theo, 2),
                        "mid": (bid + ask) / 2,
                        "spread_pct_mid": (ask - bid) / ((bid + ask) / 2),
                        "quote_time": now,
                        "quote_age_seconds": 10.0,
                        "deals": 50,
                        "volume_qty": 10_000.0,
                        "vwap": theo,
                        "turnover_brl": 10_000 * theo,
                        "open_interest": np.nan,
                        "contract_size": 1.0,
                        "tick_size": 0.01,
                        "underlying_price": SPOT,
                        "read_time": now,
                    }
                )
    return pd.DataFrame(rows)[list(CHAIN_COLUMNS)]


@pytest.fixture
def chain(calendar: B3Calendar) -> pd.DataFrame:
    return synthetic_chain(calendar)


def make_params(direction: Direction, flow: Flow, **kw) -> AnalysisParams:
    s = SETTINGS
    defaults = dict(
        direction=direction,
        flow=flow,
        quantity=100,
        rate_annual=RATE_ANNUAL,
        liquidity=LiquidityRules(
            max_spread_pct_mid=0.5,
            min_mid_price_brl=0.03,
            min_turnover_brl=0,
            min_deals=1,
            max_quote_age_seconds=300,
        ),
        weights=s.analysis.weights.model_dump(),
        pricing=s.pricing,
        early_exercise=s.early_exercise,
        dte_min=1,
        dte_max=90,
        max_width=5.0,
    )
    defaults.update(kw)
    return AnalysisParams(**defaults)
