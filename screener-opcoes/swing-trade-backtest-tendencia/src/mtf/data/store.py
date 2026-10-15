"""Leitura e gravação das barras em data/raw/{SYMBOL}_{TF}.parquet."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from mtf.models import BAR_COLUMNS, TIMEFRAME_DELTA, TIMEFRAMES, MarketData

log = logging.getLogger(__name__)


def prepare_bars(raw: pd.DataFrame, timeframe: str, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Ordena, remove duplicadas e descarta barras ainda em formação.

    `close_time` = abertura + duração do timeframe. Uma barra cujo close_time é posterior ao
    instante do download (`cutoff`) não estava fechada e nunca entra no backtest.
    """
    bars = raw.sort_values("time").copy()
    duplicated = bars["time"].duplicated(keep="last")
    if duplicated.any():
        log.warning("%s: %d barras duplicadas removidas", timeframe, int(duplicated.sum()))
        bars = bars[~duplicated]
    bars["close_time"] = bars["time"] + TIMEFRAME_DELTA[timeframe]
    incomplete = bars["close_time"] > cutoff
    if incomplete.any():
        log.info("%s: %d barra(s) em formação descartada(s)", timeframe, int(incomplete.sum()))
        bars = bars[~incomplete]
    return bars[list(BAR_COLUMNS)].reset_index(drop=True)


def bars_path(raw_dir: Path, symbol: str, timeframe: str) -> Path:
    return raw_dir / f"{symbol}_{timeframe}.parquet"


def save_bars(
    raw: pd.DataFrame, symbol: str, timeframe: str, raw_dir: Path, cutoff: pd.Timestamp
) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    bars = prepare_bars(raw, timeframe, cutoff)
    bars.to_parquet(bars_path(raw_dir, symbol, timeframe), index=False)
    return bars


def load_bars(raw_dir: Path, symbol: str, timeframe: str) -> pd.DataFrame:
    return pd.read_parquet(bars_path(raw_dir, symbol, timeframe))


def available_symbols(raw_dir: Path) -> list[str]:
    """Ativos com os três timeframes gravados."""
    names = {path.stem.rsplit("_", 1)[0] for path in raw_dir.glob("*_H1.parquet")}
    return sorted(
        name for name in names if all(bars_path(raw_dir, name, tf).exists() for tf in TIMEFRAMES)
    )


def load_market_data(raw_dir: Path, symbol: str) -> MarketData:
    return MarketData(
        symbol=symbol,
        d1=load_bars(raw_dir, symbol, "D1"),
        h4=load_bars(raw_dir, symbol, "H4"),
        h1=load_bars(raw_dir, symbol, "H1"),
    )
