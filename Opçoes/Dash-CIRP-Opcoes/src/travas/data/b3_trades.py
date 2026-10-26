"""Fechamento oficial do pregão pela B3 (arquivo público "TradeInformationConsolidatedFile").

Uma linha por instrumento negociado no dia: mínimo, máximo, preço médio, último negócio, preço
de referência, nº de negócios, quantidade e volume financeiro. NÃO traz bid/ask nem o horário dos
negócios. Conferido em 18/10/2026: o "Último" das opções no ProfitChart com o mercado fechado
bate com `LastPric` deste arquivo (82 de 82 séries de BBAS3 do pregão de 16/10).

Fonte padrão com o mercado fechado: cada perna é avaliada pelo último negócio do dia
(indicativo, marcado `price_basis = "ultimo_b3"`) e o ativo pelo seu fechamento. Mesmo download
do cadastro de instrumentos (token → CSV, latin-1, ';', 1ª linha "Status do Arquivo: …"). Só o
que interessa é guardado em `data/b3/negocios_<data>.csv`: ações/ETFs (CASH) e opções com
negócio no dia.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import logging
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.b3_instruments import BASE, MAX_LOOKBACK_SESSIONS

log = logging.getLogger(__name__)

FILE_NAME = "TradeInformationConsolidatedFile"
SEGMENTS = ("CASH", "EQUITY CALL", "EQUITY PUT")
COLUMNS = {
    "TckrSymb": "symbol",
    "SgmtNm": "segment",
    "MinPric": "min",
    "MaxPric": "max",
    "TradAvrgPric": "avg",
    "LastPric": "last",
    "RefPric": "ref",
    "TradQty": "deals",
    "FinInstrmQty": "qty",
    "NtlFinVol": "turnover_brl",
}
NUMERIC = ["min", "max", "avg", "last", "ref", "deals", "qty", "turnover_brl"]
RETRY_MISSING_SECONDS = 15 * 60  # dia ainda não publicado: tenta de novo depois disso


def parse_trades(data: bytes) -> pd.DataFrame | None:
    """CSV da B3 → instrumentos com negócio no dia (índice = symbol). None se o arquivo não
    estiver com status final (ainda em produção) ou vier vazio."""
    text = data.decode("latin-1")
    status, _, body = text.partition("\n")
    if "final" not in status.lower() or not body.strip():
        return None
    raw = pd.read_csv(
        io.StringIO(body), sep=";", usecols=list(COLUMNS), dtype=str, low_memory=False
    ).rename(columns=COLUMNS)
    raw = raw[raw["segment"].isin(SEGMENTS)]
    for col in NUMERIC:
        raw[col] = pd.to_numeric(
            raw[col].str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
            errors="coerce",
        )
    traded = raw[raw["last"].notna() & (raw["last"] > 0)]
    return traded.drop_duplicates("symbol").set_index("symbol")


class B3Trades:
    def __init__(self, directory: Path, calendar: B3Calendar, timeout: float = 90.0) -> None:
        self._dir = directory
        self._calendar = calendar
        self._timeout = timeout
        self._lock = threading.Lock()
        self._memo: tuple[dt.date, pd.DataFrame] | None = None
        self._missing: dict[dt.date, float] = {}  # dia → monotonic da última tentativa sem arquivo

    def _path(self, day: dt.date) -> Path:
        return self._dir / f"negocios_{day.isoformat()}.csv"

    def _read_cache(self, day: dt.date) -> pd.DataFrame:
        return pd.read_csv(self._path(day), index_col="symbol")

    def _download(self, day: dt.date) -> pd.DataFrame | None:
        url = f"{BASE}/requestname?fileName={FILE_NAME}&date={day.isoformat()}"
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
            token = json.loads(resp.read().decode("utf-8")).get("token")
        if not token:
            return None
        with urllib.request.urlopen(f"{BASE}/?token={token}", timeout=self._timeout) as resp:  # noqa: S310
            data = resp.read()
        if len(data) < 1000:  # arquivo ainda não publicado para o dia
            return None
        return parse_trades(data)

    def fetch(self, day: dt.date) -> pd.DataFrame | None:
        """Arquivo de um pregão específico, sem cache (None se não publicado ou sem acesso)."""
        try:
            return self._download(day)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            log.warning("B3: negócios de %s indisponíveis: %s", day, exc)
            return None

    def latest(self, today: dt.date) -> tuple[dt.date, pd.DataFrame] | None:
        """Pregão mais recente (hoje, se já publicado, ou até 5 anteriores) com arquivo final.
        Cache em disco por dia; o dia de hoje sem arquivo é tentado de novo a cada 15 min."""
        candidates = ([today] if self._calendar.is_session(today) else []) + list(
            reversed(self._calendar.previous_sessions(today, MAX_LOOKBACK_SESSIONS))
        )
        with self._lock:
            for day in candidates:
                if self._memo and self._memo[0] == day:
                    return self._memo
                if self._path(day).exists():
                    return self._remember(day, self._read_cache(day))
                tried = self._missing.get(day)
                if tried is not None and time.monotonic() - tried < RETRY_MISSING_SECONDS:
                    continue
                try:
                    table = self._download(day)
                except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                    log.warning("B3: negócios de %s indisponíveis: %s", day, exc)
                    table = None
                if table is None:
                    self._missing[day] = time.monotonic()
                    continue
                self._dir.mkdir(parents=True, exist_ok=True)
                table.to_csv(self._path(day))
                for old in self._dir.glob("negocios_*.csv"):
                    if old != self._path(day):
                        old.unlink(missing_ok=True)
                log.info("B3: fechamento de %s (%d instrumentos negociados)", day, len(table))
                return self._remember(day, table)
            return None

    def _remember(self, day: dt.date, table: pd.DataFrame) -> tuple[dt.date, pd.DataFrame]:
        self._memo = (day, table)
        return self._memo


def closing_chain(
    catalog: pd.DataFrame,
    trades: pd.DataFrame,
    session: dt.date,
    underlying: str,
    today: dt.date,
    calendar: B3Calendar,
    columns: list[str],
) -> tuple[pd.DataFrame, float | None]:
    """Cadeia de `underlying` (séries vigentes do catálogo) avaliada pelo fechamento da B3.

    bid/ask/mid ficam ausentes (o arquivo não os traz: nada é inventado); `last` = último
    negócio do dia, `price_basis = "ultimo_b3"` faz a análise usá-lo como preço indicativo.
    Negócios/volume são os do dia inteiro. Séries sem negócio no dia ficam sem preço. Devolve
    a cadeia e o fechamento do ativo."""
    opts = catalog[
        (catalog["underlying"] == underlying) & (catalog["expiration_date"] >= today)
    ].reset_index(drop=True)
    stock = trades["last"].get(underlying)
    spot = float(stock) if stock is not None and pd.notna(stock) else None
    if opts.empty:
        return pd.DataFrame(columns=[*columns, "price_basis"]), spot
    day = trades.reindex(opts["symbol"]).reset_index(drop=True)
    expirations = pd.Series(opts["expiration_date"])
    nan = float("nan")
    frame = opts.assign(
        dte_business_days=calendar.sessions_until(today, expirations).to_numpy(),
        dte_calendar_days=(pd.to_datetime(expirations) - pd.Timestamp(today)).dt.days.to_numpy(),
        bid=nan,
        ask=nan,
        last=day["last"].to_numpy(dtype="float64"),
        mid=nan,
        spread_pct_mid=nan,
        book_crossed=False,
        quote_time=pd.NaT,
        quote_age_seconds=nan,
        deals=day["deals"].fillna(0).to_numpy(dtype="int64"),
        volume_qty=day["qty"].to_numpy(dtype="float64"),
        vwap=day["avg"].to_numpy(dtype="float64"),
        turnover_brl=day["turnover_brl"].fillna(0).to_numpy(dtype="float64"),
        open_interest=nan,
        tick_size=0.01,
        underlying_price=spot if spot is not None else nan,
        read_time=pd.Timestamp(session),
        volume_source=f"B3 (pregão de {session:%d/%m/%Y})",
        price_basis="ultimo_b3",
    )
    frame["quote_time"] = pd.Series(
        pd.NaT, index=frame.index, dtype="datetime64[ns, America/Sao_Paulo]"
    )
    out = frame[[*columns, "price_basis"]]
    return out.sort_values(["expiration_date", "option_type", "strike"]).reset_index(
        drop=True
    ), spot
