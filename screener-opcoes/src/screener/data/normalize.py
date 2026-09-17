"""Transforma registros brutos do symbol_info nas tabelas documentadas em schema.py."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from screener.calendar_b3 import B3Calendar
from screener.data.schema import OPTIONS_COLUMNS
from screener.timeutils import server_epoch_to_local

OPTION_TYPE_BY_RIGHT = {0: "call", 1: "put"}
EXERCISE_STYLE_BY_MODE = {0: "european", 1: "american"}


def zero_as_missing(values: pd.Series) -> pd.Series:
    return values.astype("float64").where(values != 0)


def reference_price(last: pd.Series, bid: pd.Series, ask: pd.Series) -> pd.Series:
    """Último negócio; se ausente, mid do book. Entradas já com zero → NaN."""
    return last.fillna((bid + ask) / 2)


def option_catalog(symbols: pd.DataFrame, server_timezone: str) -> pd.DataFrame:
    """Campos estáticos das opções listadas (sem cotações), a partir do symbols_get."""
    options = symbols[symbols["option_strike"] > 0]
    expiration = server_epoch_to_local(options["expiration_time"].to_numpy(), server_timezone)
    return pd.DataFrame(
        {
            "symbol": options["name"].to_numpy(),
            "underlying": options["basis"].to_numpy(),
            "description": options["description"].to_numpy(),
            "option_type": options["option_right"].map(OPTION_TYPE_BY_RIGHT).to_numpy(),
            "exercise_style": options["option_mode"].map(EXERCISE_STYLE_BY_MODE).to_numpy(),
            "strike": options["option_strike"].to_numpy(dtype="float64"),
            "expiration_time": expiration.array,
            "expiration_date": expiration.dt.date.to_numpy(),
        }
    )


def normalize_options(
    raw: pd.DataFrame,
    snapshot_time: pd.Timestamp,
    snapshot_date: dt.date,
    server_timezone: str,
    calendar: B3Calendar,
) -> pd.DataFrame:
    """`raw`: symbol_info das séries + read_time + underlying_bid/ask/last/time (valores brutos)."""
    raw = raw.reset_index(drop=True)
    catalog = option_catalog(raw, server_timezone)
    bid, ask, last = (zero_as_missing(raw[c]) for c in ("bid", "ask", "last"))
    has_book = bid.notna() & ask.notna()
    mid = ((bid + ask) / 2).where(has_book)
    quote_time = server_epoch_to_local(raw["time"].to_numpy(), server_timezone)
    read_time = raw["read_time"]
    # Idade medida no relógio do servidor: referência = tick mais recente lido no mesmo lote
    # (séries + ativo-objeto). Evita confundir defasagem entre o PC e o servidor com cotação velha.
    batch_latest = raw.groupby("read_time")["time"].transform("max")
    reference_epoch = pd.concat([batch_latest, raw["underlying_time"]], axis=1).max(axis=1)
    quote_age = (reference_epoch - raw["time"]).where(raw["time"] > 0)
    volume_qty = raw["session_volume"].astype("float64")
    vwap = zero_as_missing(raw["session_aw"])
    contract_size = raw["trade_contract_size"].astype("float64")
    u_bid, u_ask, u_last = (
        zero_as_missing(raw[c]) for c in ("underlying_bid", "underlying_ask", "underlying_last")
    )
    expiration_days = pd.to_datetime(catalog["expiration_date"])

    frame = catalog.assign(
        snapshot_time=snapshot_time,
        read_time=read_time,
        dte_business_days=calendar.sessions_until(snapshot_date, catalog["expiration_date"]),
        dte_calendar_days=(expiration_days - pd.Timestamp(snapshot_date)).dt.days,
        bid=bid.to_numpy(),
        ask=ask.to_numpy(),
        last=last.to_numpy(),
        mid=mid.to_numpy(),
        spread_pct_mid=((ask - bid) / mid).to_numpy(),
        quote_time=quote_time,
        quote_age_seconds=quote_age.astype("float64").to_numpy(),
        deals=raw["session_deals"].astype("int64").to_numpy(),
        volume_qty=volume_qty.to_numpy(),
        vwap=vwap.to_numpy(),
        turnover_brl=(volume_qty * vwap.fillna(0) * contract_size).to_numpy(),
        prev_close=zero_as_missing(raw["session_close"]).to_numpy(),
        open_interest=zero_as_missing(raw["session_interest"]).to_numpy(),
        contract_size=contract_size.to_numpy(),
        tick_size=raw["trade_tick_size"].astype("float64").to_numpy(),
        underlying_bid=u_bid.to_numpy(),
        underlying_ask=u_ask.to_numpy(),
        underlying_last=u_last.to_numpy(),
        underlying_price=reference_price(u_last, u_bid, u_ask).to_numpy(),
    )
    return frame[list(OPTIONS_COLUMNS)].astype({"description": "string"})
