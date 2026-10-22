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
    "volume_source": "Origem de negócios/volume: sessão (symbol_info) ou barra D1 de hoje",
    "ref_note": "Divergência do MT5 corrigida pela B3 (strike/vencimento); nulo se ok",
}


def _volume_fallback(raw: pd.DataFrame) -> pd.DataFrame:
    """Algumas corretoras (ex.: Genial) não preenchem session_deals/volume/aw nas opções. Nesses
    casos usa a barra D1 de hoje da própria opção: negócios ≈ tick_volume, quantidade =
    real_volume, preço médio ≈ fechamento da barra (aproximação, marcada em volume_source)."""
    raw = raw.copy()
    raw["volume_source"] = "sessão"
    if "d1_real_volume" not in raw:
        return raw
    empty = (raw["session_volume"] == 0) & (raw["session_deals"] == 0)
    use = empty & raw["d1_real_volume"].fillna(0).gt(0)
    raw.loc[use, "session_deals"] = raw.loc[use, "d1_tick_volume"]
    raw.loc[use, "session_volume"] = raw.loc[use, "d1_real_volume"]
    raw.loc[use, "session_aw"] = raw.loc[use, "d1_close"]
    raw.loc[use, "volume_source"] = "barra D1"
    raw.loc[empty & ~use, "volume_source"] = "sem negócios hoje"
    return raw


def zero_as_missing(values: pd.Series) -> pd.Series:
    values = values.astype("float64")
    return values.where(values != 0)


def reference_price(last: pd.Series, bid: pd.Series, ask: pd.Series) -> pd.Series:
    """Último negócio; se ausente, mid do book."""
    return last.fillna((bid + ask) / 2)


UNDERLYING_TICKER_RE = r"[A-Z0-9]{4}\d{1,2}"  # PETR4, BOVA11, TAEE11, AAPL34…

# Ativo-objeto como a B3 o cadastra → símbolo de onde vem o PREÇO (cotação e candles). As opções
# de Ibovespa têm ativo "IBOV11", mas o subjacente é o índice IBOV: no MT5 da XP o IBOV11 só
# recebe o fechamento uma vez por dia (e tem histórico curto), o IBOV é o índice ao vivo.
PRICE_SYMBOLS = {"IBOV11": "IBOV"}


def price_symbol(underlying: str) -> str:
    return PRICE_SYMBOLS.get(underlying.upper(), underlying)


# Opções sobre índice: vencimento mensal na quarta-feira mais próxima do dia 15 (as de ações e
# ETFs vencem na 3ª sexta-feira).
INDEX_OPTION_UNDERLYINGS = frozenset({"IBOV11"})


def resolve_underlying(
    names: pd.Series, basis: pd.Series, reference: pd.DataFrame | None
) -> pd.Series:
    """Ativo-objeto de cada opção: o mapa oficial da B3 (ticker → ativo) prevalece; sem ele, o
    `basis` do MT5 quando tem formato de ticker de ativo. Corrige corretoras que preenchem o
    `basis` com o próprio ticker da opção (ex.: Genial: "YDUQK886"). Sem resolução → NaN."""
    mapped = names.map(reference["underlying"]) if reference is not None else names.map({})
    valid_basis = basis.where(basis.fillna("").str.fullmatch(UNDERLYING_TICKER_RE))
    return mapped.fillna(valid_basis)


def option_catalog(
    symbols: pd.DataFrame, server_timezone: str, reference: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Campos estáticos das opções de ações/ETFs/índice (symbols_get): option_strike > 0 e grupo
    BOVESPA (opções da BM&F, ex. dólar, ficam fora). Séries sem ativo-objeto resolvido saem."""
    options = symbols[symbols["option_strike"] > 0]
    if "path" in options:
        options = options[options["path"].fillna("").str.startswith("BOVESPA")]
    underlying = resolve_underlying(options["name"], options["basis"], reference)
    options = options[underlying.notna()]
    underlying = underlying[underlying.notna()]
    expiration = server_epoch_to_local(options["expiration_time"].to_numpy(), server_timezone)
    catalog = pd.DataFrame(
        {
            "symbol": options["name"].to_numpy(),
            "underlying": underlying.to_numpy(),
            "option_type": options["option_right"].map(OPTION_TYPE_BY_RIGHT).to_numpy(),
            "exercise_style": options["option_mode"].map(EXERCISE_STYLE_BY_MODE).to_numpy(),
            "strike": options["option_strike"].to_numpy(dtype="float64"),
            "expiration_date": expiration.dt.date.to_numpy(),
            "contract_size": options["trade_contract_size"].to_numpy(dtype="float64"),
        }
    )
    return apply_reference(catalog, reference)


STRIKE_TOLERANCE = 0.005


def apply_reference(catalog: pd.DataFrame, reference: pd.DataFrame | None) -> pd.DataFrame:
    """Strike, vencimento e estilo oficiais da B3 prevalecem sobre o MT5; a divergência fica
    registrada em `ref_note` (nulo quando bate ou quando a série não está na referência)."""
    catalog = catalog.copy()
    catalog["ref_note"] = None
    if reference is None or catalog.empty:
        return catalog
    ref = reference.reindex(catalog["symbol"])
    has = ref["strike"].notna().to_numpy()
    notes: list[str | None] = []
    for i, (mt5_k, b3_k, mt5_d, b3_d) in enumerate(
        zip(
            catalog["strike"],
            ref["strike"],
            catalog["expiration_date"],
            ref["expiration_date"],
            strict=True,
        )
    ):
        if not has[i]:
            notes.append(None)
            continue
        parts = []
        if abs(float(mt5_k) - float(b3_k)) > STRIKE_TOLERANCE:
            parts.append(f"strike corrigido pela B3 (MT5 informava {mt5_k:.2f})".replace(".", ","))
        if pd.notna(b3_d) and mt5_d != b3_d:
            parts.append(f"vencimento corrigido pela B3 (MT5 informava {mt5_d:%d/%m/%Y})")
        notes.append("; ".join(parts) or None)
    catalog.loc[has, "strike"] = ref["strike"].to_numpy()[has]
    catalog.loc[has, "expiration_date"] = ref["expiration_date"].to_numpy()[has]
    style = ref["exercise_style"].to_numpy()
    valid_style = has & pd.notna(style)
    catalog.loc[valid_style, "exercise_style"] = style[valid_style]
    catalog["ref_note"] = pd.Series(notes, index=catalog.index, dtype=object)
    return catalog


def normalize_chain(
    raw: pd.DataFrame,
    today: dt.date,
    server_timezone: str,
    calendar: B3Calendar,
    reference: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """`raw`: symbol_info das séries + read_time + underlying_bid/ask/last/time (brutos), e
    opcionalmente d1_tick_volume/d1_real_volume/d1_close (barra D1 de hoje da opção)."""
    if raw.empty:
        return pd.DataFrame(columns=list(CHAIN_COLUMNS))
    raw = raw.reset_index(drop=True)
    if "path" in raw:  # mesmas regras do catálogo, alinhando as linhas
        keep = (
            raw["path"].fillna("").str.startswith("BOVESPA")
            & resolve_underlying(raw["name"], raw["basis"], reference).notna()
        )
        raw = raw[keep].reset_index(drop=True)
        if raw.empty:
            return pd.DataFrame(columns=list(CHAIN_COLUMNS))
    raw = _volume_fallback(raw)
    catalog = option_catalog(raw, server_timezone, reference)
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
        volume_source=raw["volume_source"].to_numpy(),
        ref_note=catalog["ref_note"].to_numpy(),
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
    "h1": pd.Timedelta(hours=1),
}  # "mn1": duração variável, tratada à parte (até o 1º dia do mês seguinte)


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
    if timeframe == "mn1":
        start = pd.to_datetime(frame["time"], unit="s")  # relógio do servidor, sem fuso
        end_epoch = (start + pd.offsets.MonthBegin(1)).map(pd.Timestamp.timestamp)
    else:
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
