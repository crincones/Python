"""Descoberta do universo no terminal: estatísticas dos ativos-objeto e cotações das séries."""

from __future__ import annotations

import datetime as dt
import logging
import time

import pandas as pd

from screener.calendar_b3 import B3Calendar
from screener.collector.mt5_client import MT5Client, MT5Error
from screener.data.normalize import reference_price, zero_as_missing
from screener.data.schema import BARS_COLUMNS
from screener.settings import Settings
from screener.timeutils import LOCAL_TIMEZONE, server_epoch_to_local
from screener.universe_rules import average_daily_turnover

log = logging.getLogger(__name__)

QUOTE_FIELDS = ["bid", "ask", "last"]
PARTIAL_BARS = 1  # a barra D1 do dia corrente, ainda em formação


def _daily_turnover_with_retries(
    client: MT5Client, underlying: str, expected: list[dt.date], settings: Settings
) -> dict:
    stats: dict = {}
    for attempt in range(1, settings.collector.history_retries + 1):
        try:
            rates = client.daily_rates(underlying, len(expected) + PARTIAL_BARS)
        except MT5Error:
            rates = pd.DataFrame()
        stats = average_daily_turnover(rates, expected)
        if not stats["missing_sessions"]:
            return stats
        log.info(
            "%s: faltam %d pregões no D1 (tentativa %d); aguardando sincronização",
            underlying,
            len(stats["missing_sessions"]),
            attempt,
        )
        time.sleep(settings.mt5.retry_wait_seconds)
    log.warning("%s: histórico D1 incompleto, faltam %s", underlying, stats["missing_sessions"])
    return stats


def fetch_underlying_stats(
    client: MT5Client,
    listed_series: pd.Series,
    snapshot_date: dt.date,
    calendar: B3Calendar,
    settings: Settings,
) -> pd.DataFrame:
    """Cotação e volume financeiro médio de cada ativo-objeto com opções listadas."""
    expected = calendar.previous_sessions(
        snapshot_date, settings.underlying_filter.lookback_sessions
    )
    underlyings = listed_series.index.tolist()
    rows = []
    for batch in client.selected_batches(underlyings):
        infos = client.symbol_infos(batch)
        for _, info in infos.iterrows():
            stats = _daily_turnover_with_retries(client, info["name"], expected, settings)
            rows.append(
                {
                    "underlying": info["name"],
                    **{field: info[field] for field in QUOTE_FIELDS},
                    "time": info["time"],
                    "avg_daily_turnover_brl": stats["avg_daily_turnover_brl"],
                    "sessions_used": stats["sessions_used"],
                }
            )

    found = pd.DataFrame(
        rows,
        columns=["underlying", *QUOTE_FIELDS, "time", "avg_daily_turnover_brl", "sessions_used"],
    )
    frame = listed_series.rename("listed_series").rename_axis("underlying").reset_index()
    frame = frame.merge(found, on="underlying", how="left")
    missing = frame.loc[frame["time"].isna(), "underlying"].tolist()
    if missing:
        log.warning("Ativos-objeto sem symbol_info no servidor: %s", ", ".join(missing))

    bid, ask, last = (zero_as_missing(frame[f].fillna(0)) for f in QUOTE_FIELDS)
    server_tz = settings.mt5.server_timezone
    return frame.assign(
        bid=bid,
        ask=ask,
        last=last,
        price=reference_price(last, bid, ask),
        quote_time=server_epoch_to_local(frame["time"].fillna(0).to_numpy(), server_tz),
        sessions_expected=len(expected),
        sessions_used=frame["sessions_used"].fillna(0).astype("int64"),
        history_complete=frame["sessions_used"].fillna(0) == len(expected),
    ).drop(columns="time")


def fetch_series_quotes(client: MT5Client, underlying: str, symbols: list[str]) -> pd.DataFrame:
    """symbol_info das séries de um ativo, com a cotação do ativo lida junto de cada lote."""
    frames = []
    for _ in client.selected_batches([underlying]):  # mantém o ativo-objeto selecionado
        for batch in client.selected_batches(symbols, heartbeat=underlying):
            read_time = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
            infos = client.symbol_infos(batch)
            if infos.empty:
                continue
            spot = client.symbol_infos([underlying])
            for field in QUOTE_FIELDS:
                infos[f"underlying_{field}"] = spot[field].iloc[0] if not spot.empty else 0.0
            infos["underlying_time"] = spot["time"].iloc[0] if not spot.empty else 0
            infos["read_time"] = read_time
            frames.append(infos)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_bars(client: MT5Client, underlyings: list[str], settings: Settings) -> pd.DataFrame:
    """Barras de cada timeframe configurado em signals.timeframes (tabela schema.BARS_COLUMNS)."""
    frames = []
    for batch in client.selected_batches(underlyings):
        for underlying in batch:
            for timeframe in settings.signals.timeframes:
                try:
                    rates = client.rates(underlying, timeframe, settings.signals.bars)
                except MT5Error:
                    log.warning(
                        "%s: sem barras %s; viés automático ficará neutro", underlying, timeframe
                    )
                    continue
                if rates.empty:
                    continue
                frames.append(rates.assign(underlying=underlying, timeframe=timeframe))
    if not frames:
        return pd.DataFrame(columns=list(BARS_COLUMNS))
    bars = pd.concat(frames, ignore_index=True)
    bars["time"] = server_epoch_to_local(bars["time"].to_numpy(), settings.mt5.server_timezone)
    return bars[list(BARS_COLUMNS)]
