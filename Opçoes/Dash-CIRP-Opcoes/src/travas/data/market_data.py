"""Leituras do MT5 para um ativo-objeto: cotação, cadeia de opções e candles.

Adaptado do coletor do screener-opcoes. Recebe um MT5Client já conectado; devolve DataFrames
normalizados (normalize.py). Nenhuma cotação é inventada: série sem tick fica com NaN.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.mt5_client import MT5Client, MT5Error
from travas.data.normalize import (
    INDEX_OPTION_UNDERLYINGS,
    normalize_bars,
    normalize_chain,
    price_symbol,
    reference_price,
    zero_as_missing,
)
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE, server_epoch_to_local, server_now_epoch

log = logging.getLogger(__name__)

QUOTE_FIELDS = ["bid", "ask", "last"]
MIN_QUOTED_FRACTION = 0.30  # abaixo disso, com o ativo cotado, o feed parece parado
FEED_RETRIES = 2


@dataclass(frozen=True)
class UnderlyingQuote:
    symbol: str
    bid: float | None
    ask: float | None
    last: float | None
    price: float | None
    quote_time: pd.Timestamp | None
    pc_lag_seconds: float | None  # relógio do PC − horário do último tick
    source: str = "mt5"  # mt5 | ultimo_pregao | mt5_fora_pregao

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "price": self.price,
            "quote_time": self.quote_time.isoformat() if self.quote_time is not None else None,
            "pc_lag_seconds": self.pc_lag_seconds,
        }


def _opt(value: float) -> float | None:
    return None if pd.isna(value) else float(value)


def underlying_quote(client: MT5Client, symbol: str, server_timezone: str) -> UnderlyingQuote:
    """Cotação do ativo-objeto, lida do símbolo de preço (`price_symbol`: IBOV11 → IBOV)."""
    source = price_symbol(symbol)
    for batch in client.selected_batches([source]):
        infos = client.symbol_infos(batch)
        if infos.empty:
            break
        row = infos.iloc[0]
        bid, ask, last = (zero_as_missing(pd.Series([row[f]])) for f in QUOTE_FIELDS)
        price = reference_price(last, bid, ask).iloc[0]
        quote_time = (
            server_epoch_to_local(pd.Series([row["time"]]), server_timezone).iloc[0]
            if row["time"] > 0
            else None
        )
        lag = (
            (pd.Timestamp.now(tz=LOCAL_TIMEZONE) - quote_time).total_seconds()
            if quote_time is not None
            else None
        )
        return UnderlyingQuote(
            symbol,
            _opt(bid.iloc[0]),
            _opt(ask.iloc[0]),
            _opt(last.iloc[0]),
            _opt(price),
            quote_time,
            lag,
        )
    raise MT5Error(f"ativo {source} não encontrado no terminal")


def _attach_d1(client: MT5Client, infos: pd.DataFrame, server_tz: str) -> pd.DataFrame:
    """Para séries sem negócios/volume da sessão, lê a barra D1 de HOJE da própria opção."""
    infos = infos.copy()
    for col in ("d1_tick_volume", "d1_real_volume", "d1_close"):
        infos[col] = float("nan")
    today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
    empty = (infos["session_volume"] == 0) & (infos["session_deals"] == 0) & (infos["time"] > 0)
    for idx in infos.index[empty]:
        try:
            rates = client.rates(infos.at[idx, "name"], "d1", 1)
        except MT5Error:
            continue
        if rates.empty:
            continue
        bar = rates.iloc[-1]
        bar_day = server_epoch_to_local(pd.Series([bar["time"]]), server_tz).iloc[0].date()
        if bar_day == today:
            infos.at[idx, "d1_tick_volume"] = float(bar["tick_volume"])
            infos.at[idx, "d1_real_volume"] = float(bar["real_volume"])
            infos.at[idx, "d1_close"] = float(bar["close"])
    return infos


def fetch_series_quotes(
    client: MT5Client,
    underlying: str,
    symbols: list[str],
    server_tz: str = LOCAL_TIMEZONE,
    d1_fallback: bool = True,
) -> pd.DataFrame:
    """symbol_info das séries, com a cotação do ativo lida junto de cada lote.

    `d1_fallback=False` dispensa a barra D1 das séries sem negócios na sessão (necessária só em
    corretoras que não preenchem session_*, como a Genial; na XP cada consulta de série sem
    barra falha com "Call failed" e custa ~1 s)."""
    frames = []
    source = price_symbol(underlying)
    for _ in client.selected_batches([source]):  # mantém o ativo-objeto selecionado
        for batch in client.selected_batches(symbols, heartbeat=source):
            read_time = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
            infos = client.symbol_infos(batch)
            if infos.empty:
                continue
            spot = client.symbol_infos([source])
            for field in QUOTE_FIELDS:
                infos[f"underlying_{field}"] = spot[field].iloc[0] if not spot.empty else 0.0
            infos["underlying_time"] = spot["time"].iloc[0] if not spot.empty else 0
            infos["read_time"] = read_time
            frames.append(_attach_d1(client, infos, server_tz) if d1_fallback else infos)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def feed_problem(raw: pd.DataFrame) -> str | None:
    if raw.empty:
        return "nenhuma série lida"
    underlying_quoted = (raw[["underlying_bid", "underlying_ask", "underlying_last"]] > 0).any(
        axis=1
    )
    if not underlying_quoted.all():
        return "ativo-objeto sem cotação durante a leitura"
    fraction = float((raw["time"] > 0).mean())
    if fraction < MIN_QUOTED_FRACTION:
        return f"só {fraction:.0%} das séries com tick"
    return None


@dataclass(frozen=True)
class ChainScope:
    """O que coletar: classe(s) de opção, prazo máximo (dias úteis), faixa absoluta de strikes e,
    opcionalmente, só os N próximos vencimentos MENSAIS mais os semanais com até
    `weekly_max_dte` dias úteis (anteriores ao último mensal escolhido)."""

    option_types: tuple[str, ...]
    max_dte: int
    strike_low: float
    strike_high: float
    monthly_expirations: int | None = None
    weekly_max_dte: int = 0


def candidate_symbols(
    catalog: pd.DataFrame,
    underlying: str,
    scope: ChainScope,
    today: dt.date,
    calendar: B3Calendar,
) -> pd.DataFrame:
    """Séries do catálogo dentro do escopo (vencimentos ainda não expirados)."""
    frame = catalog[
        (catalog["underlying"] == underlying) & catalog["option_type"].isin(scope.option_types)
    ].copy()
    if frame.empty:
        return frame
    frame = frame[frame["expiration_date"] >= today]
    frame["dte_business_days"] = calendar.sessions_until(
        today, pd.Series(frame["expiration_date"].to_numpy(), index=frame.index)
    )
    keep = frame["dte_business_days"] <= scope.max_dte
    keep &= frame["strike"].between(scope.strike_low, scope.strike_high)
    if scope.monthly_expirations is not None:
        keep &= frame["expiration_date"].isin(
            select_expirations(
                frame["expiration_date"].unique(),
                today,
                calendar,
                scope.monthly_expirations,
                scope.weekly_max_dte,
                index=underlying.upper() in INDEX_OPTION_UNDERLYINGS,
            )
        )
    return frame[keep]


def select_expirations(
    expirations,
    today: dt.date,
    calendar: B3Calendar,
    monthly: int,
    weekly_max_dte: int,
    index: bool = False,
) -> set[dt.date]:
    """Os `monthly` próximos vencimentos mensais e os de curto prazo (semanais; diários no
    índice) com até `weekly_max_dte` dias úteis que vençam antes do último mensal escolhido.
    Mensal: 3ª sexta-feira (ações/ETFs) ou quarta-feira mais próxima do dia 15 (`index`)."""
    ordered = sorted(d for d in expirations if d >= today)
    is_monthly = calendar.is_index_monthly_expiration if index else calendar.is_monthly_expiration
    months = [d for d in ordered if is_monthly(d)][:monthly]
    if not months:  # padrão de vencimento desconhecido: os N mais próximos
        return set(ordered[:monthly])
    dte = calendar.sessions_until(today, pd.Series(ordered))
    weeklies = {
        d
        for d, n in zip(ordered, dte, strict=True)
        if d not in months and n <= weekly_max_dte and d < months[-1]
    }
    return set(months) | weeklies


def fetch_chain(
    client: MT5Client,
    catalog: pd.DataFrame,
    underlying: str,
    scope: ChainScope,
    calendar: B3Calendar,
    settings: Settings,
    reference: pd.DataFrame | None = None,
    d1_fallback: bool = True,
) -> pd.DataFrame:
    today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
    candidates = candidate_symbols(catalog, underlying, scope, today, calendar)
    if candidates.empty:
        return normalize_chain(pd.DataFrame(), today, settings.mt5.server_timezone, calendar)
    symbols = candidates["symbol"].tolist()
    log.info("%s: coletando %d séries", underlying, len(symbols))
    problem = None
    for attempt in range(1, FEED_RETRIES + 1):
        raw = fetch_series_quotes(
            client, underlying, symbols, settings.mt5.server_timezone, d1_fallback
        )
        problem = feed_problem(raw)
        if problem is None:
            return normalize_chain(raw, today, settings.mt5.server_timezone, calendar, reference)
        log.warning("%s: %s (tentativa %d)", underlying, problem, attempt)
        client.cool_down()
    raise MT5Error(f"feed do MT5 com problema em {underlying}: {problem}")


def fetch_bars(client: MT5Client, underlying: str, timeframe: str, count: int, server_tz: str):
    source = price_symbol(underlying)  # IBOV11 → candles do índice IBOV
    for _ in client.selected_batches([source]):
        rates = client.rates(source, timeframe, count)
        return normalize_bars(rates, timeframe, server_tz, server_now_epoch(server_tz))
    raise MT5Error(f"ativo {source} não pôde ser selecionado")


def fetch_daily_set(
    client: MT5Client, tickers: list[str], count: int, server_tz: str
) -> dict[str, tuple[pd.DataFrame, dict]]:
    """Barras D1 + campos da sessão (negócios, descrição) de vários ativos, num só lote."""
    now_epoch = server_now_epoch(server_tz)
    out: dict[str, tuple[pd.DataFrame, dict]] = {}
    for batch in client.selected_batches(tickers):
        infos = client.symbol_infos(batch)
        by_name = {row["name"]: row for _, row in infos.iterrows()} if not infos.empty else {}
        for name in batch:
            try:
                rates = client.rates(name, "d1", count)
            except MT5Error:
                log.warning("%s: sem barras D1", name)
                continue
            info = by_name.get(name)
            out[name] = (
                normalize_bars(rates, "d1", server_tz, now_epoch),
                {
                    "description": str(info["description"]).strip() if info is not None else None,
                    "session_deals": float(info["session_deals"]) if info is not None else None,
                },
            )
    return out
