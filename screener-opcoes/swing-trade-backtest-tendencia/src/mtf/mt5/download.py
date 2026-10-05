"""Download do universo e das barras D1/H4/H1 para data/raw/ (Parquet)."""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import pandas as pd

from mtf.config import Settings, data_dir
from mtf.data.store import prepare_bars, save_bars
from mtf.data.timeutils import mt5_epoch_to_local, now_local
from mtf.mt5.client import MT5Client
from mtf.universe.selection import average_daily_value, rank_universe

log = logging.getLogger(__name__)


def _raw_bars(client: MT5Client, symbol: str, timeframe: str, settings: Settings) -> pd.DataFrame:
    start = dt.datetime.combine(settings.data.start_date, dt.time())
    end_date = settings.data.end_date or dt.date.today()
    end = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time())
    rates = client.rates_range(symbol, timeframe, start, end)
    if rates.empty:
        return rates
    rates["time"] = mt5_epoch_to_local(rates["time"].to_numpy(), settings.mt5.server_timezone)
    return rates


def optionable_stocks(client: MT5Client, settings: Settings) -> pd.DataFrame:
    """Ações à vista que são ativo-objeto de pelo menos uma opção listada."""
    symbols = client.symbols()
    folder = symbols["path"].str.rsplit("\\", n=1).str[0]
    options = symbols[(folder == settings.universe.options_path) & (symbols["option_strike"] > 0)]
    series_count = options.groupby("basis").size().rename("listed_options")
    stocks = symbols.loc[folder == settings.universe.stock_path, ["name", "path", "description"]]
    stocks = stocks[
        stocks["name"].isin(series_count.index) & ~stocks["name"].isin(settings.universe.excluded)
    ]
    return (
        stocks.rename(columns={"name": "symbol"})
        .merge(series_count, left_on="symbol", right_index=True)
        .assign(options_available=True)
        .reset_index(drop=True)
    )


def download(settings: Settings, pilot: int | None = None, raw_dir: Path | None = None) -> Path:
    """Baixa D1 de todo o universo com opções, ranqueia pela liquidez e baixa H4/H1 dos
    selecionados. Grava data/metadata/universe.parquet e download.json."""
    raw_dir = raw_dir or data_dir() / "raw"
    meta_dir = data_dir() / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    pilot = settings.universe.pilot_assets if pilot is None else pilot
    cutoff = now_local()

    with MT5Client(settings.mt5) as client:
        stocks = optionable_stocks(client, settings)
        log.info("%d ações com opções listadas", len(stocks))
        daily: dict[str, pd.DataFrame] = {}
        for symbol in stocks["symbol"]:
            client.select(symbol)
            bars = _raw_bars(client, symbol, "D1", settings)
            if bars.empty:
                log.warning("%s: sem barras D1", symbol)
                continue
            daily[symbol] = bars
        completed = {s: prepare_bars(b, "D1", cutoff) for s, b in daily.items()}
        adv = {
            symbol: average_daily_value(bars, settings.universe.liquidity_window)
            for symbol, bars in completed.items()
        }
        universe = rank_universe(stocks, adv, settings.universe.min_average_daily_value)
        chosen = universe[universe["eligible"]]["symbol"].tolist()
        if pilot:
            chosen = chosen[:pilot]
        universe["selected"] = universe["symbol"].isin(chosen)

        for symbol in chosen:
            client.select(symbol)
            save_bars(daily[symbol], symbol, "D1", raw_dir, cutoff)
            for timeframe in settings.data.timeframes:
                if timeframe == "D1":
                    continue
                bars = _raw_bars(client, symbol, timeframe, settings)
                if bars.empty:
                    log.warning("%s: sem barras %s", symbol, timeframe)
                    continue
                save_bars(bars, symbol, timeframe, raw_dir, cutoff)
            log.info("%s: barras gravadas", symbol)
        build = client.terminal_build()

    universe.to_parquet(meta_dir / "universe.parquet", index=False)
    meta = {
        "downloaded_at": cutoff.isoformat(),
        "terminal_build": build,
        "start_date": settings.data.start_date.isoformat(),
        "end_date": (settings.data.end_date or cutoff.date()).isoformat(),
        "timeframes": settings.data.timeframes,
        "selected": chosen,
        "pilot_assets": pilot,
    }
    (meta_dir / "download.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return raw_dir
