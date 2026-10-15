"""Registros brutos do symbol_info → tabelas normalizadas (sem dependência do MT5).

Colunas da cadeia (`CHAIN_COLUMNS`), uma linha por série. Zero vindo do MT5 em campos de preço,
volume e OI significa ausente → NaN. Timestamps em America/Sao_Paulo.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.timeutils import server_epoch_to_local

OPTION_TYPE_BY_RIGHT = {0: "call", 1: "put"}  # SYMBOL_OPTION_RIGHT_CALL/PUT
EXERCISE_STYLE_BY_MODE = {0: "european", 1: "american"}  # SYMBOL_OPTION_MODE_*

CHAIN_COLUMNS: dict[str, str] = {
    "symbol": "Ticker da opção (nome real no servidor)",
    "underlying": "Ativo-objeto (campo basis)",
    "option_type": "call ou put (option_right)",
    "exercise_style": "american ou european (option_mode)",
    "strike": "Preço de exercício (option_strike, relido a cada coleta)",
    "expiration_date": "Data de vencimento (expiration_time)",
    "dte_business_days": "Pregões após hoje até o vencimento, inclusive",
    "dte_calendar_days": "Dias corridos até o vencimento",
    "bid": "Melhor oferta de compra (NaN se zero)",
    "ask": "Melhor oferta de venda (NaN se zero)",
    "last": "Último negócio (NaN se zero)",
    "mid": "(bid + ask)/2; NaN se bid ou ask ausente ou ask < bid",
    "spread_pct_mid": "(ask − bid)/mid",
    "quote_time": "Horário do último tick da série",
    "quote_age_seconds": "Segundos entre o tick da série e o tick mais recente do mesmo lote",
    "deals": "Negócios na sessão (session_deals)",
    "volume_qty": "Quantidade negociada na sessão (session_volume)",
    "vwap": "Preço médio da sessão (session_aw; NaN se zero)",
    "turnover_brl": "Volume financeiro = volume_qty × vwap × contract_size",
    "open_interest": "Contratos em aberto (session_interest; NaN se zero — ausente na XP)",
    "contract_size": "trade_contract_size (unidades do ativo por opção)",
    "tick_size": "trade_tick_size",
    "underlying_price": "Último do ativo-objeto (ou mid) lido junto com a série",
    "read_time": "Momento da leitura no terminal (relógio do PC)",
}


def zero_as_missing(values: pd.Series) -> pd.Series:
    values = values.astype("float64")
    return values.where(values != 0)


def reference_price(last: pd.Series, bid: pd.Series, ask: pd.Series) -> pd.Series:
    """Último negócio; se ausente, mid do book."""
    return last.fillna((bid + ask) / 2)


def option_catalog(symbols: pd.DataFrame, server_timezone: str) -> pd.DataFrame:
    """Campos estáticos de todas as opções listadas (symbols_get). Opção = option_strike > 0."""
    options = symbols[symbols["option_strike"] > 0]
    expiration = server_epoch_to_local(options["expiration_time"].to_numpy(), server_timezone)
    return pd.DataFrame(
        {
            "symbol": options["name"].to_numpy(),
            "underlying": options["basis"].to_numpy(),
            "option_type": options["option_right"].map(OPTION_TYPE_BY_RIGHT).to_numpy(),
            "exercise_style": options["option_mode"].map(EXERCISE_STYLE_BY_MODE).to_numpy(),
            "strike": options["option_strike"].to_numpy(dtype="float64"),
            "expiration_date": expiration.dt.date.to_numpy(),
            "contract_size": options["trade_contract_size"].to_numpy(dtype="float64"),
        }
    )


def normalize_chain(
    raw: pd.DataFrame, today: dt.date, server_timezone: str, calendar: B3Calendar
) -> pd.DataFrame:
    """`raw`: symbol_info das séries + read_time + underlying_bid/ask/last/time (brutos)."""
    if raw.empty:
        return pd.DataFrame(columns=list(CHAIN_COLUMNS))
    raw = raw.reset_index(drop=True)
    catalog = option_catalog(raw, server_timezone)
    bid, ask, last = (zero_as_missing(raw[c]) for c in ("bid", "ask", "last"))
    has_book = bid.notna() & ask.notna() & (ask >= bid)
    mid = ((bid + ask) / 2).where(has_book)
    # Idade no relógio do servidor: referência = tick mais recente do mesmo lote (séries + ativo).
    batch_latest = raw.groupby("read_time")["time"].transform("max")
    reference_epoch = pd.concat([batch_latest, raw["underlying_time"]], axis=1).max(axis=1)
    quote_age = (reference_epoch - raw["time"]).where(raw["time"] > 0)
    volume_qty = raw["session_volume"].astype("float64")
    vwap = zero_as_missing(raw["session_aw"])
    contract_size = raw["trade_contract_size"].astype("float64")
    u_bid, u_ask, u_last = (
        zero_as_missing(raw[c]) for c in ("underlying_bid", "underlying_ask", "underlying_last")
    )
    expirations = pd.Series(catalog["expiration_date"])
    frame = catalog.assign(
        dte_business_days=calendar.sessions_until(today, expirations).to_numpy(),
        dte_calendar_days=(pd.to_datetime(expirations) - pd.Timestamp(today)).dt.days.to_numpy(),
        bid=bid.to_numpy(),
        ask=ask.to_numpy(),
        last=last.to_numpy(),
        mid=mid.to_numpy(),
        spread_pct_mid=((ask - bid) / mid).to_numpy(),
        quote_time=server_epoch_to_local(raw["time"].to_numpy(), server_timezone).array,
        quote_age_seconds=quote_age.astype("float64").to_numpy(),
        deals=raw["session_deals"].astype("int64").to_numpy(),
        volume_qty=volume_qty.to_numpy(),
        vwap=vwap.to_numpy(),
        turnover_brl=(volume_qty * vwap.fillna(0) * contract_size).to_numpy(),
        open_interest=zero_as_missing(raw["session_interest"]).to_numpy(),
        contract_size=contract_size.to_numpy(),
        tick_size=raw["trade_tick_size"].astype("float64").to_numpy(),
        underlying_price=reference_price(u_last, u_bid, u_ask).to_numpy(),
        read_time=raw["read_time"].to_numpy(),
    )
    return (
        frame[list(CHAIN_COLUMNS)]
        .sort_values(["expiration_date", "option_type", "strike"])
        .reset_index(drop=True)
    )


BAR_PERIODS = {
    "d1": pd.Timedelta(days=1),
    "w1": pd.Timedelta(days=7),
    "h4": pd.Timedelta(hours=4),
}


def normalize_bars(
    rates: pd.DataFrame, timeframe: str, server_timezone: str, now_server_epoch: float
) -> pd.DataFrame:
    """copy_rates → time (America/Sao_Paulo), OHLC, volumes e `forming`.

    `forming` = o período da barra ainda não terminou no relógio do servidor (a última barra
    pode estar em formação; a D1 fica marcada até a meia-noite mesmo após o fechamento).
    Nenhuma barra é criada para preencher lacunas.
    """
    if rates.empty:
        return pd.DataFrame(
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                "real_volume",
                "forming",
            ]
        )
    frame = rates.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    end_epoch = frame["time"] + BAR_PERIODS[timeframe].total_seconds()
    return pd.DataFrame(
        {
            "time": server_epoch_to_local(frame["time"].to_numpy(), server_timezone).array,
            "open": frame["open"].astype("float64"),
            "high": frame["high"].astype("float64"),
            "low": frame["low"].astype("float64"),
            "close": frame["close"].astype("float64"),
            "tick_volume": frame["tick_volume"].astype("float64"),
            "real_volume": frame["real_volume"].astype("float64"),
            "forming": end_epoch > now_server_epoch,
        }
    )


def ema(close: pd.Series, span: int) -> pd.Series:
    """EMA com α = 2/(n+1), semente = primeiro fechamento (pandas ewm adjust=False).

    Os primeiros `span` valores ficam NaN (aquecimento), para não exibir uma média ainda
    dominada pela semente.
    """
    values = close.astype("float64").ewm(span=span, adjust=False).mean()
    values.iloc[:span] = float("nan")
    return values
