"""Serviço de dados de mercado para a API: uma conexão MT5, acesso serializado por trava.

A API do MetaTrader5 não é thread-safe; toda chamada passa por `self._lock`. A conexão é aberta
em segundo plano na inicialização (pode abrir o terminal) e o estado fica disponível em
`status()` para a interface mostrar conectando / conectado / erro.
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from dataclasses import dataclass, field

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data import market_data
from travas.data.b3_instruments import B3Instruments
from travas.data.b3_trades import B3Trades, closing_chain
from travas.data.mt5_client import MT5Client, MT5Error
from travas.data.normalize import (
    CHAIN_COLUMNS,
    ema,
    normalize_chain,
    option_catalog,
    price_symbol,
)
from travas.data.quote_store import QuoteStore, reference_capture
from travas.data.snapshots import Snapshot, SnapshotSource, snapshot_chain
from travas.market_hours import MarketStatus, market_status, parse_hhmm
from travas.settings import Settings
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)

OFF_HOURS_SOURCES = ("b3", "capturas", "servidor")


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
        self._daily_cache: dict[tuple, tuple] = {}
        self._quotes = QuoteStore(settings.paths.quotes_dir)
        self._instruments = B3Instruments(settings.paths.quotes_dir.parent / "b3", self._calendar)
        self._trades = B3Trades(settings.paths.quotes_dir.parent / "b3", self._calendar)
        self._snapshots = SnapshotSource(
            settings.snapshots.server_url,
            settings.paths.snapshots_dir,
            settings.snapshots.timeout_seconds,
        )
        self._off_hours_source = settings.collection.off_hours_source
        self._clock = lambda: pd.Timestamp.now(tz=LOCAL_TIMEZONE).to_pydatetime()

    def market(self) -> MarketStatus:
        h = self._settings.market_hours
        return market_status(
            self._clock(), self._calendar, parse_hhmm(h.session_open), parse_hhmm(h.session_close)
        )

    @property
    def calendar(self) -> B3Calendar:
        return self._calendar

    @property
    def instruments(self) -> B3Instruments:
        return self._instruments

    @property
    def off_hours_source(self) -> str:
        return self._off_hours_source

    def set_off_hours_source(self, source: str) -> None:
        if source not in OFF_HOURS_SOURCES:
            raise ValueError(f"fonte desconhecida: {source}")
        with self._lock:
            if source != self._off_hours_source:
                self._off_hours_source = source
                self._chains = {}

    def _closing(self, underlying: str, today: dt.date) -> tuple[tuple | None, str | None]:
        """Fechamento da B3 a usar com o mercado fechado: ((pregão, negócios), None), ou
        (None, motivo) quando indisponível — aí valem as capturas salvas. Um arquivo mais velho
        que as capturas do ativo (o do último pregão ainda não publicado) não é usado."""
        if self._off_hours_source != "b3":
            return None, None
        found = self._trades.latest(today)
        if found is None:
            return None, "fechamento da B3 indisponível (arquivo não publicado ou sem acesso)"
        day, _ = found
        _, captured = self._quotes.spot(underlying)
        if captured is not None and pd.Timestamp(captured).date() > day:
            return None, (
                f"fechamento da B3 de {pd.Timestamp(captured):%d/%m} ainda não publicado "
                f"(último disponível: {day:%d/%m}); usando as capturas do pregão"
            )
        return found, None

    def _snapshot(self, underlying: str) -> tuple[Snapshot | None, str | None]:
        """Snapshot do servidor a usar com o mercado fechado: (snapshot, nota), ou (None, motivo)
        quando indisponível ou mais velho que as capturas locais do ativo — aí valem elas."""
        if self._off_hours_source != "servidor":
            return None, None
        snap = self._snapshots.latest()
        if snap is None:
            reason = self._snapshots.problem or "nenhum snapshot no servidor"
            return None, f"snapshot do servidor indisponível ({reason}); usando as capturas"
        if not (snap.frame["underlying"] == underlying).any():
            return None, (
                f"snapshot do servidor de {snap.label} sem {underlying} (fora dos ativos com "
                "opções no MT5 do servidor); usando as capturas"
            )
        _, captured = self._quotes.spot(underlying)
        if captured is not None and pd.Timestamp(captured) > snap.captured_at:
            return None, (
                f"capturas locais ({pd.Timestamp(captured):%d/%m %H:%M}) mais recentes que o "
                f"snapshot do servidor ({snap.label}); usando as capturas"
            )
        return snap, snap.note

    def _close_time(self, day: dt.date) -> pd.Timestamp:
        close = parse_hhmm(self._settings.market_hours.session_close)
        return pd.Timestamp(dt.datetime.combine(day, close)).tz_localize(LOCAL_TIMEZONE)

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
            self._daily_cache: dict[tuple, tuple] = {}
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
            "off_hours_source": self._off_hours_source,
            "snapshot": self._snapshot_status(),
            "broker": self.broker_name(),
        }

    def latest_snapshot(self) -> Snapshot | None:
        """Snapshot mais recente do servidor, qualquer que seja a fonte escolhida (uso
        informativo, ex.: qualidade do book na aba Liquidez de Opções)."""
        return self._snapshots.latest()

    def _snapshot_status(self) -> dict | None:
        """Snapshot em uso (só com a fonte "servidor" e o mercado fechado)."""
        if self._off_hours_source != "servidor" or self.market().is_open:
            return None
        snap = self._snapshots.latest()
        if snap is None:
            return {"available": False, "problem": self._snapshots.problem}
        return {"available": True, "label": snap.label, "status": snap.status, "note": snap.note}

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
            today = pd.Timestamp.now(tz=LOCAL_TIMEZONE).date()
            closing, _ = self._closing(underlying, today)
            if closing is not None and underlying in closing[1].index:
                day, trades = closing
                close = float(trades.at[underlying, "last"])
                return market_data.UnderlyingQuote(
                    underlying,
                    None,
                    None,
                    close,
                    close,
                    self._close_time(day),
                    None,
                    "fechamento_b3",
                )
            snap, _ = self._snapshot(underlying)
            if snap is not None:
                _, spot = snapshot_chain(snap.frame, underlying, today, self._calendar)
                if spot is not None:
                    return market_data.UnderlyingQuote(
                        underlying,
                        None,
                        None,
                        None,
                        spot,
                        snap.captured_at,
                        None,
                        "snapshot_servidor",
                    )
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
            closing, closing_note = (
                (None, None) if market.is_open else self._closing(underlying, started.date())
            )
            snap, snap_note = (None, None) if market.is_open else self._snapshot(underlying)
            closed_chain = closed_spot = snap_chain = snap_spot = None
            if snap is not None:
                snap_chain, snap_spot = snapshot_chain(
                    snap.frame, underlying, started.date(), self._calendar
                )
            if closing is not None:
                try:
                    closed_chain, closed_spot = closing_chain(
                        self.catalog(),
                        closing[1],
                        closing[0],
                        underlying,
                        started.date(),
                        self._calendar,
                        list(CHAIN_COLUMNS),
                    )
                except MarketDataUnavailable as exc:
                    closing_note = f"fechamento da B3 sem a lista de séries do MT5 ({exc})"
            stored = (
                None
                if market.is_open or closed_chain is not None or snap_chain is not None
                else self._quotes.load(underlying, started.date(), self._calendar)
            )
            stored_spot = None
            if closed_chain is not None:
                chain, stored_spot = _filter_scope(closed_chain, effective), closed_spot
                source = "fechamento_b3"
            elif snap_chain is not None:
                chain, stored_spot = _filter_scope(snap_chain, effective), snap_spot
                source = "snapshot_servidor"
            elif stored is not None:
                chain, stored_spot = QuoteStore.align_captures(_filter_scope(stored, effective))
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
                "spot": stored_spot or chain_spot(chain, source, quote.price),
                "underlying": quote.to_dict(),
                "collected_at": finished.isoformat(),
                "duration_seconds": round((finished - started).total_seconds(), 1),
                "series": len(chain),
                "series_with_book": int(chain["mid"].notna().sum()) if len(chain) else 0,
                "realtime_warning": _join_notes(
                    _source_warning(source, chain, market, self._settings),
                    closing_note,
                    snap_note,
                )
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
        """Cotações de séries específicas (carteira). Coluna `source` indica a origem.

        Pregão aberto: MT5 (e salva). Fora do pregão: últimas cotações salvas; só as séries
        nunca capturadas no pregão são lidas do MT5, marcadas como `mt5_fora_pregao`.
        """
        now = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
        market = self.market()
        frames = []
        missing = list(symbols)
        if not market.is_open:
            closing, _ = self._closing(underlying, now.date())
            if closing is not None:
                try:
                    catalog = self.catalog()
                except MarketDataUnavailable:
                    catalog = None
                if catalog is not None:
                    closed, _ = closing_chain(
                        catalog[catalog["symbol"].isin(missing)],
                        closing[1],
                        closing[0],
                        underlying,
                        now.date(),
                        self._calendar,
                        list(CHAIN_COLUMNS),
                    )
                    frames.append(closed.assign(source="fechamento_b3"))
                    missing = [s for s in missing if s not in set(closed["symbol"])]
            snap, _ = self._snapshot(underlying)
            if snap is not None and missing:
                rows, _ = snapshot_chain(snap.frame, underlying, now.date(), self._calendar)
                hit = rows[rows["symbol"].isin(missing)].assign(source="snapshot_servidor")
                frames.append(hit)
                missing = [s for s in missing if s not in set(hit["symbol"])]
            stored = self._quotes.load(underlying, now.date(), self._calendar)
            if stored is not None and missing:
                hit, _ = QuoteStore.align_captures(stored[stored["symbol"].isin(missing)])
                hit = hit.assign(source="ultimo_pregao")
                frames.append(hit)
                missing = [s for s in missing if s not in set(hit["symbol"])]
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
        """Barras D1 (300) e negócios da sessão de vários ativos (heatmap, IV/HV da liquidez).
        Cache por lista de ativos: 60 s com o pregão aberto; 15 min fora dele."""
        market = self.market()
        ttl = 60 if market.is_open else 900
        key = tuple(sorted(tickers))
        cached = self._daily_cache.get(key)
        if cached and time.monotonic() - cached[0] <= ttl:
            return cached[1], {**cached[2], "from_cache": True}
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
        if len(self._daily_cache) >= 4:
            self._daily_cache.clear()
        self._daily_cache[key] = (time.monotonic(), data, meta)
        return data, meta

    def candles(self, underlying: str, timeframe: str) -> tuple[pd.DataFrame, dict]:
        s = self._settings.candles
        requested = s.monthly_bars if timeframe == "mn1" else s.bars
        with self._lock:
            client = self._require()
            try:
                bars = market_data.fetch_bars(
                    client, underlying, timeframe, requested, self._settings.mt5.server_timezone
                )
            except MT5Error as exc:
                raise MarketDataUnavailable(str(exc)) from exc
        bars = bars.assign(
            ema_fast=ema(bars["close"], s.ema_fast), ema_slow=ema(bars["close"], s.ema_slow)
        )
        meta = {
            "timeframe": timeframe,
            "price_symbol": price_symbol(underlying),
            "bars": len(bars),
            "requested": requested,
            "last_bar_time": bars["time"].iloc[-1].isoformat() if len(bars) else None,
            "last_bar_forming": bool(bars["forming"].iloc[-1]) if len(bars) else None,
            "ema_fast": s.ema_fast,
            "ema_slow": s.ema_slow,
            "ema_method": (
                "EMA α = 2/(n+1), semente no 1º fechamento coletado, "
                "primeiros n valores ocultos (aquecimento)"
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


def chain_spot(chain: pd.DataFrame, source: str, fallback: float | None) -> float | None:
    """Preço do ativo coerente com as cotações das opções.

    Cotações salvas (fora do pregão): `fallback` (a cadeia usa o da captura de referência,
    `QuoteStore.align_captures`). Coleta ao vivo: o lido junto com o lote mais recente
    (nunca uma linha qualquer da cadeia, que pode ser de outro lote)."""
    if source == "ultimo_pregao" or chain.empty or not chain["underlying_price"].notna().any():
        return fallback
    rows = chain[chain["underlying_price"].notna()]
    latest = rows.loc[pd.to_datetime(rows["read_time"]).idxmax()]
    return float(latest["underlying_price"])


def _join_notes(*notes: str | None) -> str | None:
    return "; ".join(n for n in notes if n) or None


def _source_warning(
    source: str, chain: pd.DataFrame, market: MarketStatus, settings: Settings
) -> str | None:
    if source == "snapshot_servidor":
        when = f"{chain['captured_at'].min():%d/%m/%Y %H:%M}" if len(chain) else "—"
        return (
            f"{market.label}: snapshot do servidor de {when} (bid/ask do MT5 naquele horário), "
            f"com os {settings.snapshots.expirations} próximos vencimentos mensais (e semanais "
            f"até {settings.snapshots.weekly_max_business_days} du) e strikes a até "
            f"{settings.collection.strike_range_pct_spot:.0%} do spot. Não são cotações atuais"
        )
    if source == "fechamento_b3":
        day = pd.Timestamp(chain["read_time"].iloc[0]) if len(chain) else None
        when = f" do pregão de {day:%d/%m/%Y}" if day is not None else ""
        return (
            f"{market.label}: fechamento oficial da B3{when}, com cada série pelo último negócio "
            "do dia e o ativo pelo fechamento (como o ProfitChart com o mercado fechado). Preços "
            "indicativos: o arquivo não traz bid/ask nem horário, e os negócios podem ter sido "
            "em horários diferentes"
        )
    if source == "ultimo_pregao":
        captured = pd.to_datetime(chain["captured_at"]) if len(chain) else None
        # Horário da captura de referência (a com mais séries), a mesma do preço do ativo.
        when = (
            reference_capture(captured).strftime("%d/%m/%Y %H:%M") if captured is not None else "—"
        )
        span = ""
        if captured is not None and captured.max() - captured.min() > pd.Timedelta(minutes=5):
            span = (
                f"; as séries foram capturadas entre {captured.min():%d/%m %H:%M} e "
                f"{captured.max():%d/%m %H:%M}; a idade de cada uma é medida contra a captura "
                "com mais séries, e as distantes dela além do limite ficam como cotação antiga "
                "(não são combinadas como se fossem do mesmo momento)"
            )
        return (
            f"{market.label}: usando as últimas cotações capturadas no pregão ({when}){span}. "
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
