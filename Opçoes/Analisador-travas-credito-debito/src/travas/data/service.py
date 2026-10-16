"""Serviço de dados de mercado para a API: uma conexão MT5, acesso serializado por trava.

A API do MetaTrader5 não é thread-safe; toda chamada passa por `self._lock`. A conexão é aberta
em segundo plano na inicialização (pode abrir o terminal) e o estado fica disponível em
`status()` para a interface mostrar conectando / conectado / erro.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data import market_data
from travas.data.b3_instruments import B3Instruments
from travas.data.mt5_client import MT5Client, MT5Error
from travas.data.normalize import ema, normalize_chain, option_catalog
from travas.data.quote_store import QuoteStore
from travas.market_hours import MarketStatus, market_status, parse_hhmm
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)


class MarketDataUnavailable(RuntimeError):
    """MT5 desconectado ou dado não disponível; a mensagem é exibida ao usuário."""


@dataclass
class _State:
    phase: str = "desconectado"  # desconectado | conectando | conectado | erro
    error: str | None = None
    terminal: dict = field(default_factory=dict)
    connected_at: pd.Timestamp | None = None


class MarketDataService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._calendar = B3Calendar.from_csv(settings.paths.holidays_file)
        self._lock = threading.RLock()
        self._client: MT5Client | None = None
        self._state = _State()
        self._catalog: pd.DataFrame | None = None
        self._catalog_time = 0.0
        self._chains: dict[tuple, tuple[float, pd.DataFrame, dict]] = {}
        self._account_key: tuple | None = None
        self._daily_cache = None
        self._quotes = QuoteStore(settings.paths.quotes_dir)
        self._instruments = B3Instruments(settings.paths.quotes_dir.parent / "b3", self._calendar)
        self._clock = lambda: pd.Timestamp.now(tz=LOCAL_TIMEZONE).to_pydatetime()

    def market(self) -> MarketStatus:
        h = self._settings.market_hours
        return market_status(
            self._clock(), self._calendar, parse_hhmm(h.session_open), parse_hhmm(h.session_close)
        )

    @property
    def calendar(self) -> B3Calendar:
        return self._calendar

    # ---- conexão ---------------------------------------------------------------------------
    def connect_in_background(self) -> None:
        threading.Thread(target=self._connect_safely, name="mt5-connect", daemon=True).start()

    def _connect_safely(self) -> None:
        try:
            self.connect()
        except (MT5Error, OSError) as exc:
            log.error("Falha ao conectar ao MT5: %s", exc)

    def connect(self) -> None:
        with self._lock:
            if self._client is not None:
                return
            self._state = _State(phase="conectando")
            client = MT5Client(self._settings.mt5)
            try:
                client.__enter__()
                terminal = client.terminal_summary()
            except (MT5Error, OSError) as exc:
                self._state = _State(phase="erro", error=_diagnostic(exc))
                raise
            self._client = client
            self._account_key = (terminal["server"], terminal["login"])
            # Login da conta não é exibido nem logado além do necessário.
            self._state = _State(
                phase="conectado",
                terminal={
                    "build": terminal["build"],
                    "server": terminal["server"],
                    "company": terminal["company"],
                    "connected": terminal["connected"],
                },
                connected_at=pd.Timestamp.now(tz=LOCAL_TIMEZONE),
            )

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                self._client.__exit__(None, None, None)
                self._client = None
                self._state = _State()

    def _require(self) -> MT5Client:
        if self._client is None:
            phase = self._state.phase
            detail = self._state.error or "conexão ainda não estabelecida"
            raise MarketDataUnavailable(f"MT5 {phase}: {detail}")
        if not self._client.is_connected():
            # IPC com o terminal pode cair (ex.: "IPC recv failed"); reinicializa a API uma vez.
            log.warning("MT5 sem conexão (%s); reinicializando a API", self._client.last_error())
            self._client.close()
            try:
                self._client.connect()
            except MT5Error as exc:
                raise MarketDataUnavailable(f"falha ao reconectar ao MT5: {exc}") from exc
            if not self._client.is_connected():
                raise MarketDataUnavailable(
                    "terminal MT5 sem conexão com o servidor da corretora (ou API sem IPC)"
                )
        return self._client

    def _catalog_from_terminal(self) -> pd.DataFrame:
        for attempt in (1, 2):
            client = self._require()
            try:
                today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
                return option_catalog(
                    client.symbols(),
                    self._settings.mt5.server_timezone,
                    self._instruments.reference(today),
                )
            except MT5Error as exc:
                if attempt == 2:
                    raise MarketDataUnavailable(str(exc)) from exc
                client.close()  # força reconexão no próximo _require
        raise AssertionError("inalcançável")

    def _check_account(self) -> None:
        """A conta logada no terminal pode mudar (ex.: XP → Genial no mesmo terminal). Quando muda,
        atualiza o estado e descarta caches montados com a corretora anterior."""
        try:
            summary = self._client.terminal_summary()
        except MT5Error:
            return
        current = (summary["server"], summary["login"])
        if self._account_key is not None and current != self._account_key:
            log.info("Conta do MT5 mudou para %s: caches descartados", summary["server"])
            self._catalog = None
            self._chains = {}
            self._daily_cache = None
        self._account_key = current
        self._state.terminal = {
            "build": summary["build"],
            "server": summary["server"],
            "company": summary["company"],
            "connected": summary["connected"],
        }

    def broker_name(self) -> str:
        """Nome curto da corretora da conta logada (ex.: "XP Investimentos")."""
        company = (self._state.terminal or {}).get("company") or "corretora"
        return " ".join(company.split()[:2])

    def status(self) -> dict:
        s = self._state
        connected_now = None
        if s.phase == "conectado" and self._lock.acquire(timeout=0.5):
            try:
                connected_now = self._client is not None and self._client.is_connected()
                if connected_now:
                    self._check_account()
            finally:
                self._lock.release()
        return {
            "phase": s.phase,
            "error": s.error,
            "terminal": s.terminal,
            "server_connected": connected_now,
            "busy": connected_now is None and s.phase == "conectado",
            "connected_at": s.connected_at.isoformat() if s.connected_at is not None else None,
            "now": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
            "is_session_today": self._calendar.is_session(
                pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
            ),
            "market": self.market().to_dict(),
            "broker": self.broker_name(),
        }

    # ---- dados -----------------------------------------------------------------------------
    def catalog(self) -> pd.DataFrame:
        with self._lock:
            ttl = self._settings.collection.catalog_cache_minutes * 60
            if self._catalog is None or time.monotonic() - self._catalog_time > ttl:
                self._catalog = self._catalog_from_terminal()
                self._catalog_time = time.monotonic()
                log.info("Catálogo: %d opções listadas", len(self._catalog))
            return self._catalog

    def underlyings(self) -> pd.DataFrame:
        """Todos os ativos com opções listadas: lista e nº de séries da B3 (arquivo oficial),
        marcando os que têm opções no MT5 da corretora logada (`has_mt5_options`). Sem o
        arquivo da B3, cai para a lista do MT5."""
        catalog = self.catalog()
        today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
        return merge_underlyings(catalog, *self._instruments.summary(today), today)

    def quote(self, underlying: str) -> market_data.UnderlyingQuote:
        """Cotação do ativo. Fora do pregão: último preço salvo durante o pregão, se houver."""
        if not self.market().is_open:
            price, captured = self._quotes.spot(underlying)
            if price is not None:
                return market_data.UnderlyingQuote(
                    underlying, None, None, None, price, captured, None, "ultimo_pregao"
                )
        with self._lock:
            client = self._require()
            try:
                quote = market_data.underlying_quote(
                    client, underlying, self._settings.mt5.server_timezone
                )
            except MT5Error as exc:
                raise MarketDataUnavailable(str(exc)) from exc
        if not self.market().is_open:
            return market_data.UnderlyingQuote(**{**quote.__dict__, "source": "mt5_fora_pregao"})
        return quote

    def default_scope(self, spot: float) -> market_data.ChainScope:
        c = self._settings.collection
        return market_data.ChainScope(
            ("call", "put"),
            c.max_dte_business_days,
            spot * (1 - c.strike_range_pct_spot),
            spot * (1 + c.strike_range_pct_spot),
        )

    def chain(
        self,
        underlying: str,
        scope: market_data.ChainScope | None = None,
        force: bool = False,
    ) -> tuple[pd.DataFrame, dict]:
        """Cadeia de opções do ativo no escopo pedido (com cache curto) e metadados da coleta."""
        with self._lock:
            key = (underlying, scope)
            cached = self._chains.get(key)
            ttl = self._settings.collection.chain_cache_seconds
            if cached and not force and time.monotonic() - cached[0] <= ttl:
                return cached[1], {**cached[2], "from_cache": True}
            quote = self.quote(underlying)
            if quote.price is None:
                raise MarketDataUnavailable(f"{underlying} sem cotação no terminal")
            started = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
            effective = scope or self.default_scope(quote.price)
            market = self.market()
            stored = (
                None
                if market.is_open
                else self._quotes.load(underlying, started.date(), self._calendar)
            )
            if stored is not None:
                chain = _filter_scope(stored, effective)
                source = "ultimo_pregao"
            else:
                client = self._require()
                try:
                    chain = market_data.fetch_chain(
                        client,
                        self.catalog(),
                        underlying,
                        effective,
                        self._calendar,
                        self._settings,
                        self._instruments.reference(started.date()),
                    )
                except MT5Error as exc:
                    raise MarketDataUnavailable(str(exc)) from exc
                source = "mt5" if market.is_open else "mt5_fora_pregao"
                if market.is_open:
                    self._quotes.save(underlying, chain, started)
            finished = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
            meta = {
                "underlying": quote.to_dict(),
                "collected_at": finished.isoformat(),
                "duration_seconds": round((finished - started).total_seconds(), 1),
                "series": len(chain),
                "series_with_book": int(chain["mid"].notna().sum()) if len(chain) else 0,
                "realtime_warning": _source_warning(source, chain, market)
                or _realtime_warning(quote, self._settings),
                "source": source,
                "market": market.to_dict(),
                "scope": {
                    "option_types": list(effective.option_types),
                    "max_dte": effective.max_dte,
                    "strike_low": round(effective.strike_low, 2),
                    "strike_high": round(effective.strike_high, 2),
                },
                "from_cache": False,
            }
            self._chains = {k: v for k, v in self._chains.items() if k[0] == underlying}
            self._chains[key] = (time.monotonic(), chain, meta)
            return chain, meta

    def leg_quotes(self, underlying: str, symbols: list[str]) -> pd.DataFrame:
        """Cotações de séries específicas (acompanhamento). Coluna `source` indica a origem.

        Pregão aberto: MT5 (e salva). Fora do pregão: últimas cotações salvas; só as séries
        nunca capturadas no pregão são lidas do MT5, marcadas como `mt5_fora_pregao`.
        """
        now = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
        market = self.market()
        frames = []
        missing = list(symbols)
        if not market.is_open:
            stored = self._quotes.load(underlying, now.date(), self._calendar)
            if stored is not None:
                hit = stored[stored["symbol"].isin(symbols)].assign(source="ultimo_pregao")
                frames.append(hit)
                missing = [s for s in symbols if s not in set(hit["symbol"])]
        if missing:
            with self._lock:
                client = self._require()
                try:
                    raw = market_data.fetch_series_quotes(
                        client, underlying, missing, self._settings.mt5.server_timezone
                    )
                except MT5Error as exc:
                    raise MarketDataUnavailable(str(exc)) from exc
            fresh = normalize_chain(
                raw,
                now.date(),
                self._settings.mt5.server_timezone,
                self._calendar,
                self._instruments.reference(now.date()),
            )
            if market.is_open:
                self._quotes.save(underlying, fresh, now)
            frames.append(fresh.assign(source="mt5" if market.is_open else "mt5_fora_pregao"))
        frames = [f for f in frames if not f.empty]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def daily_set(self, tickers: list[str]) -> tuple[dict, dict]:
        """Barras D1 (300) e negócios da sessão de vários ativos, para o heatmap.
        Cache: 60 s com o pregão aberto; 15 min fora dele."""
        market = self.market()
        ttl = 60 if market.is_open else 900
        key = tuple(sorted(tickers))
        cached = self._daily_cache
        if cached and cached[0] == key and time.monotonic() - cached[1] <= ttl:
            return cached[2], {**cached[3], "from_cache": True}
        with self._lock:
            client = self._require()
            try:
                data = market_data.fetch_daily_set(
                    client, tickers, 300, self._settings.mt5.server_timezone
                )
            except MT5Error as exc:
                raise MarketDataUnavailable(str(exc)) from exc
        meta = {
            "collected_at": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
            "market": market.to_dict(),
            "from_cache": False,
        }
        self._daily_cache = (key, time.monotonic(), data, meta)
        return data, meta

    def candles(self, underlying: str, timeframe: str) -> tuple[pd.DataFrame, dict]:
        s = self._settings.candles
        with self._lock:
            client = self._require()
            try:
                bars = market_data.fetch_bars(
                    client, underlying, timeframe, s.bars, self._settings.mt5.server_timezone
                )
            except MT5Error as exc:
                raise MarketDataUnavailable(str(exc)) from exc
        bars = bars.assign(
            ema_fast=ema(bars["close"], s.ema_fast), ema_slow=ema(bars["close"], s.ema_slow)
        )
        meta = {
            "timeframe": timeframe,
            "bars": len(bars),
            "last_bar_time": bars["time"].iloc[-1].isoformat() if len(bars) else None,
            "last_bar_forming": bool(bars["forming"].iloc[-1]) if len(bars) else None,
            "ema_fast": s.ema_fast,
            "ema_slow": s.ema_slow,
            "ema_method": (
                "EMA α = 2/(n+1), semente no 1º fechamento coletado, "
                f"primeiros n valores ocultos (aquecimento); {s.bars} barras coletadas"
            ),
        }
        return bars, meta


def merge_underlyings(
    catalog: pd.DataFrame, b3: pd.DataFrame | None, b3_date, today
) -> pd.DataFrame:
    alive = catalog[catalog["expiration_date"] >= today]
    mt5 = (
        alive.groupby("underlying")
        .agg(
            mt5_series=("symbol", "size"),
            expirations=("expiration_date", "nunique"),
            mt5_next=("expiration_date", "min"),
        )
        .reset_index()
    )
    if b3 is None or b3.empty:
        merged = mt5.assign(b3_series=pd.NA, category=None, next_expiration=mt5["mt5_next"])
    else:
        merged = b3.merge(mt5, on="underlying", how="outer")
        merged["next_expiration"] = merged["mt5_next"].fillna(merged["next_expiration"])
    merged["mt5_series"] = merged["mt5_series"].fillna(0).astype(int)
    merged["has_mt5_options"] = merged["mt5_series"] > 0
    merged["listed_series"] = merged["b3_series"].fillna(merged["mt5_series"]).astype(int)
    merged = merged.drop(columns=["mt5_next"]).sort_values(
        ["listed_series", "underlying"], ascending=[False, True]
    )
    merged = merged.reset_index(drop=True)
    merged.attrs["b3_date"] = b3_date
    return merged


def _filter_scope(stored: pd.DataFrame, scope: market_data.ChainScope) -> pd.DataFrame:
    keep = stored["option_type"].isin(scope.option_types)
    keep &= stored["dte_business_days"] <= scope.max_dte
    keep &= stored["strike"].between(scope.strike_low, scope.strike_high)
    return stored[keep].reset_index(drop=True)


def _source_warning(source: str, chain: pd.DataFrame, market: MarketStatus) -> str | None:
    if source == "ultimo_pregao":
        captured = pd.Timestamp(chain["captured_at"].max()) if len(chain) else None
        when = captured.strftime("%d/%m/%Y %H:%M") if captured is not None else "—"
        return (
            f"{market.label}: usando as últimas cotações capturadas no pregão ({when}). "
            "Não são cotações atuais"
        )
    if source == "mt5_fora_pregao":
        return (
            f"{market.label} e sem cotações salvas do pregão para estas séries: valores do MT5 "
            "fora do pregão podem estar distorcidos ou ausentes"
        )
    return None


def _realtime_warning(quote: market_data.UnderlyingQuote, settings: Settings) -> str | None:
    if quote.pc_lag_seconds is None:
        return "ativo sem horário de último tick"
    limit = settings.collection.stale_feed_minutes * 60
    if quote.pc_lag_seconds > limit:
        minutes = quote.pc_lag_seconds / 60
        return (
            f"último tick do ativo há {minutes:,.0f} min: mercado fechado ou feed parado; "
            "cotações NÃO estão em tempo real".replace(",", ".")
        )
    return None


def _diagnostic(exc: BaseException) -> str:
    text = str(exc)
    hints = []
    if "IPC" in text or "-10003" in text or "-10005" in text:
        hints.append("verifique se o terminal MT5 está instalado no caminho configurado")
    if "não ficou pronto" in text:
        hints.append("o terminal abriu mas não conectou/logou a tempo; confira login e internet")
    return text + (f" — {'; '.join(hints)}" if hints else "")
