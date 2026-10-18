"""Comando `collect`: filtra o universo e grava um snapshot em Parquet."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from screener.calendar_b3 import B3Calendar
from screener.collector.mt5_client import MT5Client, MT5Error
from screener.collector.universe import fetch_bars, fetch_series_quotes, fetch_underlying_stats
from screener.data import store
from screener.data.normalize import normalize_options, option_catalog
from screener.data.schema import (
    BARS_TABLE,
    OPTIONS_COLUMNS,
    OPTIONS_TABLE,
    UNDERLYINGS_COLUMNS,
    UNDERLYINGS_TABLE,
)
from screener.market_data.b3_indicators import resolve_risk_free_rate
from screener.settings import Settings
from screener.timeutils import LOCAL_TIMEZONE
from screener.universe_rules import feed_problem, filter_underlyings, select_candidate_series

log = logging.getLogger(__name__)


def _fetch_with_feed_check(
    client: MT5Client, underlying: str, symbols: list[str], settings: Settings
) -> pd.DataFrame:
    """Lê as séries de um ativo; se o feed parecer parado, pausa e repete. Se o problema
    persistir, aborta a coleta: um snapshot com cotações faltando por falha do terminal seria
    indistinguível de séries sem liquidez."""
    problem = None
    for attempt in range(1, settings.collector.feed_retries + 1):
        raw = fetch_series_quotes(client, underlying, symbols)
        problem = feed_problem(raw, settings.collector.min_quoted_series_fraction)
        if problem is None:
            return raw
        log.warning("%s: %s (tentativa %d)", underlying, problem, attempt)
        client.cool_down()
    raise MT5Error(f"feed do MT5 com problema em {underlying}: {problem}; snapshot não gravado")


def collect_snapshot(client: MT5Client, settings: Settings) -> Path:
    snapshot_time = pd.Timestamp.now(tz=LOCAL_TIMEZONE).floor("s")
    snapshot_date = snapshot_time.date()
    server_tz = settings.mt5.server_timezone
    calendar = B3Calendar.from_csv(settings.paths.holidays_file)
    if not calendar.is_session(snapshot_date):
        log.warning("%s não é pregão: cotações podem ser do último pregão", snapshot_date)

    terminal = client.terminal_summary()
    risk_free_rate = resolve_risk_free_rate(settings.market, snapshot_date)
    catalog = option_catalog(client.symbols(), server_tz)
    listed = catalog.groupby("underlying").size().sort_values(ascending=False)
    log.info("%d opções listadas em %d ativos-objeto", len(catalog), len(listed))

    # Etapa 1: filtro inicial pela liquidez do ativo-objeto.
    stats = fetch_underlying_stats(client, listed, snapshot_date, calendar, settings)
    underlyings = filter_underlyings(stats, settings.underlying_filter)
    passed = underlyings.loc[underlyings["passed_filter"], "underlying"].tolist()
    if not passed:
        raise MT5Error("nenhum ativo-objeto aprovado (feed sem cotações?); snapshot não gravado")
    log.info("Ativos-objeto aprovados (%d): %s", len(passed), ", ".join(passed))

    spots = underlyings.set_index("underlying")["price"]
    candidates = select_candidate_series(
        catalog[catalog["underlying"].isin(passed)],
        spots,
        snapshot_date,
        calendar,
        settings.collector,
        settings.spreads,
    )
    last_expiration = candidates["expiration_date"].max() if len(candidates) else None
    if last_expiration is not None and last_expiration > calendar.last_holiday:
        log.warning(
            "Vencimento %s além do último feriado cadastrado (%s): atualizar %s",
            last_expiration,
            calendar.last_holiday,
            settings.paths.holidays_file.name,
        )

    # Etapa 2 (coleta): cotações das séries candidatas; a liquidez da série é avaliada na análise.
    raw_frames = []
    for underlying, group in candidates.groupby("underlying", sort=False):
        log.info("%s: coletando %d séries", underlying, len(group))
        raw_frames.append(
            _fetch_with_feed_check(client, str(underlying), group["symbol"].tolist(), settings)
        )

    options = (
        normalize_options(
            pd.concat(raw_frames, ignore_index=True),
            snapshot_time,
            snapshot_date,
            server_tz,
            calendar,
        )
        .sort_values(["underlying", "expiration_date", "option_type", "strike"])
        .reset_index(drop=True)
        if raw_frames
        else pd.DataFrame(columns=list(OPTIONS_COLUMNS))
    )

    bars = fetch_bars(client, passed, settings)
    log.info("Barras coletadas: %d (%s)", len(bars), ", ".join(settings.signals.timeframes))

    counts = candidates.groupby("underlying").size()
    underlyings = underlyings.assign(
        snapshot_time=snapshot_time,
        candidate_series=underlyings["underlying"].map(counts).fillna(0).astype("int64"),
    )[list(UNDERLYINGS_COLUMNS)]

    finished = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
    meta = {
        "snapshot_time": snapshot_time.isoformat(),
        "finished_time": finished.isoformat(),
        "duration_seconds": round((finished - snapshot_time).total_seconds(), 1),
        "terminal": terminal,
        "listed_options": len(catalog),
        "underlyings_total": len(underlyings),
        "underlyings_passed": len(passed),
        "series_collected": len(options),
        "bars_collected": len(bars),
        "calendar_last_holiday": calendar.last_holiday.isoformat(),
        "risk_free_rate": risk_free_rate.to_dict(),
        "settings": settings.model_dump(mode="json"),
    }
    path = store.write_snapshot(
        settings.paths.snapshots_dir,
        snapshot_time,
        {UNDERLYINGS_TABLE: underlyings, OPTIONS_TABLE: options, BARS_TABLE: bars},
        meta,
    )
    log.info(
        "Snapshot gravado em %s (%d séries, %.0f s)", path, len(options), meta["duration_seconds"]
    )
    return path
