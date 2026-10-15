"""Curvas de P&L para qualquer estrutura (trava, borboleta, calendário, perna isolada…).

- Mesmo vencimento: curva "no vencimento" = payoff exato.
- Vencimentos diferentes: a curva final é no **1º vencimento**; as pernas que vencem depois são
  avaliadas pelo modelo (Black-Scholes) — portanto também é estimativa, e é rotulada assim.
- Datas intermediárias: valor teórico Black-Scholes por perna (σ constante), um ponto por pregão.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.options import pricing
from travas.options.models import Structure
from travas.options.payoff import expiry_profile, pnl_at_expiry
from travas.options.valuation import theoretical_pnl, zero_crossings


def business_days_until(calendar: B3Calendar, day: dt.date, expiration: dt.date) -> int:
    return max(int(calendar.sessions_until(day, pd.Series([expiration])).iloc[0]), 0)


def leg_terms(structure: Structure, calendar: B3Calendar, day: dt.date) -> list[float]:
    """Prazo (anos de du) de cada perna a partir de `day`."""
    return [
        business_days_until(calendar, day, leg.expiration) / pricing.BUSINESS_DAYS_PER_YEAR
        for leg in structure.legs
    ]


def _ok(sigma: float | None) -> bool:
    return sigma is not None and math.isfinite(sigma) and sigma > 0


def price_grid(structure: Structure, extra: Sequence[float | None], points: int) -> np.ndarray:
    anchors = [*structure.strikes, *(x for x in extra if x)]
    return np.linspace(min(anchors) * 0.85, max(anchors) * 1.15, points)


def simulate(
    structure: Structure,
    today: dt.date,
    calendar: B3Calendar,
    rate: float,
    rate_annual: float,
    sigmas: Sequence[float | None],
    costs: float = 0.0,
    extra_prices: Sequence[float | None] = (),
    points: int = 161,
) -> dict:
    xs = price_grid(structure, extra_prices, points)
    first = min(structure.expirations)
    single = len(structure.expirations) == 1
    later_ok = all(
        _ok(s) for leg, s in zip(structure.legs, sigmas, strict=True) if leg.expiration > first
    )
    all_ok = all(_ok(s) for s in sigmas)

    if single:
        final = pnl_at_expiry(structure, xs, costs)
        final_label = "Payoff no vencimento (exato)"
    elif later_ok:
        final = theoretical_pnl(
            structure, xs, leg_terms(structure, calendar, first), rate, sigmas, costs
        )
        final_label = f"No 1º vencimento ({first:%d/%m}), pernas posteriores pelo modelo"
    else:
        final, final_label = None, None

    dates = []
    if all_ok:
        for day in calendar.sessions_between(today, first):
            ys = theoretical_pnl(
                structure, xs, leg_terms(structure, calendar, day), rate, sigmas, costs
            )
            dates.append(
                {
                    "date": day.isoformat(),
                    "business_days_left": business_days_until(calendar, day, first),
                    "pnl": [round(float(y), 2) for y in ys],
                    "breakevens": zero_crossings(xs, ys),
                }
            )
    vols = ", ".join(f"{s:.1%}" for s in sigmas if _ok(s)) or "indisponível"
    return {
        "available": final is not None,
        "reason": None if final is not None else "sem volatilidade para as pernas posteriores",
        "spots": [round(float(x), 4) for x in xs],
        "expiry_pnl": [round(float(y), 2) for y in final] if final is not None else [],
        "expiry_label": final_label,
        "expiry_breakevens": zero_crossings(xs, final) if final is not None else [],
        "multi_expiry": not single,
        "first_expiration": first.isoformat(),
        "dates": dates,
        "model_available": bool(dates),
        "model_reason": None if dates else "sem volatilidade confiável em todas as pernas",
        "sigmas": list(sigmas),
        "assumptions": (
            f"Valor teórico: Black-Scholes europeu por perna, σ constante ({vols}), juros "
            f"{rate_annual:.2%} a.a., sem dividendos, T = dias úteis/252. "
            + (
                "No vencimento o valor é o payoff exato."
                if single
                else "Estrutura com vencimentos diferentes: mesmo a curva do 1º vencimento "
                "depende do modelo para as pernas posteriores."
            )
        ),
    }


def profile_summary(structure: Structure, sim: dict, costs: float = 0.0) -> dict:
    """Lucro/perda máximos e breakevens: exatos se mesmo vencimento; senão estimados da curva."""
    if len(structure.expirations) == 1:
        p = expiry_profile(structure, costs)
        return {
            "max_profit": p.max_profit,
            "max_loss": p.max_loss,
            "breakevens": [round(x, 6) for x in p.breakevens],
            "reward_risk": p.reward_risk,
            "risk_reward": p.risk_reward,
            "profile_exact": True,
        }
    ys = sim["expiry_pnl"]
    if not ys:
        return {
            "max_profit": None,
            "max_loss": None,
            "breakevens": [],
            "reward_risk": None,
            "risk_reward": None,
            "profile_exact": False,
        }
    best, worst = max(ys), min(ys)
    return {
        "max_profit": best,
        "max_loss": -worst,
        "breakevens": sim["expiry_breakevens"],
        "reward_risk": best / -worst if worst < 0 and best > 0 else None,
        "risk_reward": -worst / best if worst < 0 and best > 0 else None,
        "profile_exact": False,
    }
