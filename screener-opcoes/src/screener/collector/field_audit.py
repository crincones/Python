"""Comando `check`: valida a conexão e audita quais campos de opção a corretora preenche."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from screener.collector.mt5_client import OPTION_MODE_NAMES, OPTION_RIGHT_NAMES, MT5Client
from screener.diagnostics import field_fill_rates
from screener.settings import Settings
from screener.timeutils import server_epoch_to_local, server_now_epoch

log = logging.getLogger(__name__)

# Campos numéricos em que zero significa "ausente". option_right/option_mode ficam de fora
# porque zero é um valor válido (call / europeia) e são reportados como distribuição.
AUDITED_FIELDS = [
    "bid",
    "ask",
    "last",
    "time",
    "expiration_time",
    "option_strike",
    "basis",
    "session_deals",
    "session_volume",
    "session_turnover",
    "session_aw",
    "session_close",
    "session_interest",
    "session_price_settlement",
    "price_volatility",
    "price_theoretical",
    "price_greeks_delta",
    "price_greeks_gamma",
    "price_greeks_theta",
    "price_greeks_vega",
    "price_greeks_rho",
    "price_greeks_omega",
    "price_sensitivity",
]


@dataclass(frozen=True)
class CheckReport:
    terminal: dict[str, Any]
    total_symbols: int
    total_options: int
    underlyings: pd.DataFrame
    right_mode_counts: pd.DataFrame
    sample_size: int
    fill_rates: pd.DataFrame
    median_quote_age_seconds: float
    pc_minus_server_seconds: float


def _spot_price(info: pd.Series) -> float:
    if info["last"] > 0:
        return float(info["last"])
    if info["bid"] > 0 and info["ask"] > 0:
        return float((info["bid"] + info["ask"]) / 2)
    return float("nan")


def _pick_sample(
    options: pd.DataFrame, spots: dict[str, float], per_underlying: int, now_epoch: float
) -> list[str]:
    names: list[str] = []
    for basis, group in options.groupby("basis"):
        spot = spots.get(str(basis), float("nan"))
        if pd.isna(spot):
            log.warning("Sem preço do ativo-objeto %s; fora da amostra", basis)
            continue
        alive = group[group["expiration_time"] > now_epoch]
        if alive.empty:
            continue
        nearest = alive[alive["expiration_time"] == alive["expiration_time"].min()]
        closest = (nearest["option_strike"] - spot).abs().sort_values().index[:per_underlying]
        names.extend(nearest.loc[closest, "name"].tolist())
    return names


def run_check(client: MT5Client, settings: Settings) -> CheckReport:
    server_tz = settings.mt5.server_timezone
    terminal = client.terminal_summary()

    symbols = client.symbols()
    options = symbols[symbols["option_strike"] > 0].copy()
    options["right"] = options["option_right"].map(OPTION_RIGHT_NAMES)
    options["exercise_style"] = options["option_mode"].map(OPTION_MODE_NAMES)

    underlyings = (
        options.groupby("basis")
        .size()
        .rename("listed_series")
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"basis": "underlying"})
    )
    right_mode_counts = (
        options.groupby(["right", "exercise_style"], dropna=False)
        .size()
        .rename("series")
        .reset_index()
    )

    top = underlyings["underlying"].head(settings.check.sample_underlyings).tolist()
    spots: dict[str, float] = {}
    for batch in client.selected_batches(top):
        infos = client.symbol_infos(batch)
        spots.update({row["name"]: _spot_price(row) for _, row in infos.iterrows()})

    now_epoch = server_now_epoch(server_tz)
    sample_names = _pick_sample(
        options[options["basis"].isin(top)],
        spots,
        settings.check.sample_series_per_underlying,
        now_epoch,
    )
    frames = [client.symbol_infos(batch) for batch in client.selected_batches(sample_names)]
    sample = (
        pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=AUDITED_FIELDS)
    )

    # Idade medida contra o tick mais recente da amostra (relógio do servidor). A diferença
    # entre o relógio do PC e esse tick é reportada à parte: na XP ficou em ~60–80 s.
    quoted = sample[sample["time"] > 0] if not sample.empty else sample
    if quoted.empty:
        median_age = pc_lag = float("nan")
    else:
        latest = quoted["time"].max()
        median_age = float((latest - quoted["time"]).median())
        latest_local = server_epoch_to_local(pd.Series([latest]), server_tz).iloc[0]
        pc_lag = (pd.Timestamp.now(tz=latest_local.tz) - latest_local).total_seconds()

    return CheckReport(
        terminal=terminal,
        total_symbols=len(symbols),
        total_options=len(options),
        underlyings=underlyings,
        right_mode_counts=right_mode_counts,
        sample_size=len(sample),
        fill_rates=field_fill_rates(sample, AUDITED_FIELDS),
        median_quote_age_seconds=median_age,
        pc_minus_server_seconds=pc_lag,
    )
