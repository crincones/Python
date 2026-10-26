"""Snapshots da cadeia de opções gravados no servidor e lidos pelo app (sem dependência do MT5).

O coletor (`travas snapshot`, ver `snapshot_collector.py`) roda num servidor com o MT5 em horários
fixos e grava, por pregão, um arquivo por horário com as colunas da cadeia (`CHAIN_COLUMNS`) mais
`captured_at`:

    <raiz>/2026-10-20/1100.csv.gz     cadeia (todas as séries coletadas, todos os ativos)
    <raiz>/2026-10-20/1100.json       manifesto (status, contagens, erros, terminal)
    <raiz>/2026-10-20/negocios_b3.csv fechamento oficial da B3 do pregão (`travas b3-archive`)
    <raiz>/index.json                 lista de snapshots e arquivos da B3

Arquivos de snapshot nunca são sobrescritos por outro horário: formam um histórico. O app busca
`index.json` por HTTP (rede Tailscale), baixa o snapshot mais recente para `data/snapshots/` e
monta a cadeia de cada ativo como se fosse a captura daquele horário. Nada é preenchido:
série sem cotação no snapshot continua sem cotação.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.b3_instruments import MAX_LOOKBACK_SESSIONS
from travas.data.b3_trades import B3Trades
from travas.data.normalize import CHAIN_COLUMNS, discard_crossed_book
from travas.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)

SNAPSHOT_COLUMNS = [*CHAIN_COLUMNS, "captured_at"]
TIME_COLUMNS = ("quote_time", "read_time", "captured_at")
USABLE_STATUS = ("completo", "parcial")
B3_FILE = "negocios_b3.csv"
INDEX_FILE = "index.json"
INDEX_TTL_SECONDS = 300
RETRY_AFTER_SECONDS = 120  # servidor inacessível: não tenta de novo antes disso
LOCAL_FILES_KEPT = 10


# ---- gravação (servidor) -----------------------------------------------------------------------
def _atomic_write(path: Path, write) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    write(tmp)
    os.replace(tmp, path)


def _write_json(path: Path, data: dict) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    _atomic_write(path, lambda tmp: tmp.write_text(text, encoding="utf-8"))


def write_snapshot(
    root: Path, day: dt.date, slot: str, chain: pd.DataFrame, manifest: dict
) -> dict:
    """Grava a cadeia (se houver) e o manifesto do horário `slot` (HHMM) e refaz o índice."""
    folder = root / day.isoformat()
    manifest = {**manifest, "date": day.isoformat(), "slot": slot, "file": None}
    if not chain.empty:
        rel = f"{day.isoformat()}/{slot}.csv.gz"
        frame = chain[SNAPSHOT_COLUMNS]
        _atomic_write(root / rel, lambda tmp: frame.to_csv(tmp, index=False, compression="gzip"))
        manifest["file"] = rel
    _write_json(folder / f"{slot}.json", manifest)
    write_index(root)
    return manifest


def write_index(root: Path) -> dict:
    snapshots = []
    for path in sorted(root.glob("*/*.json")):
        try:
            m = json.loads(path.read_text(encoding="utf-8"))
        except OSError, json.JSONDecodeError:
            log.warning("Manifesto ilegível: %s", path)
            continue
        snapshots.append(
            {
                k: m.get(k)
                for k in (
                    "date",
                    "slot",
                    "status",
                    "file",
                    "captured_at",
                    "finished_at",
                    "series",
                    "series_with_book",
                    "underlyings",
                    "failed",
                )
            }
        )
    trades = [
        {"date": p.parent.name, "file": f"{p.parent.name}/{p.name}"}
        for p in sorted(root.glob(f"*/{B3_FILE}"))
    ]
    index = {
        "generated_at": pd.Timestamp.now(tz=LOCAL_TIMEZONE).isoformat(),
        "snapshots": snapshots,
        "b3_trades": trades,
    }
    _write_json(root / INDEX_FILE, index)
    return index


def archive_b3_trades(root: Path, today: dt.date, calendar: B3Calendar) -> list[dt.date]:
    """Guarda o fechamento oficial da B3 dos últimos pregões que ainda não estão no arquivo.
    O arquivo do dia sai à noite; os anteriores ficam como nova tentativa."""
    days = ([today] if calendar.is_session(today) else []) + list(
        calendar.previous_sessions(today, MAX_LOOKBACK_SESSIONS)
    )
    trades = B3Trades(root / "_b3_cache", calendar)
    saved = []
    for day in days:
        path = root / day.isoformat() / B3_FILE
        if path.exists():
            continue
        table = trades.fetch(day)
        if table is None:
            log.info("B3: fechamento de %s ainda não publicado", day)
            continue
        _atomic_write(path, lambda tmp, t=table: t.to_csv(tmp))
        log.info("B3: fechamento de %s arquivado (%d instrumentos)", day, len(table))
        saved.append(day)
    write_index(root)
    return saved


def options_liquidity(
    root: Path, reference: pd.DataFrame | None, sessions: int
) -> tuple[pd.Series, list[str]]:
    """Volume financeiro médio por pregão das opções de cada ativo-objeto (maior primeiro), dos
    `sessions` fechamentos da B3 mais recentes arquivados em `root`, e as datas usadas.

    Ativo de cada opção: referência oficial (`option_reference`); séries que já venceram saem
    dela e vão pela raiz do ticker (4 letras → ativo mais comum dessa raiz)."""
    files = sorted(root.glob(f"*/{B3_FILE}"))[-sessions:]
    table = options_liquidity_table(files, reference)
    if table.empty:
        return pd.Series(dtype="float64"), []
    return table["turnover_brl"], [p.parent.name for p in files]


def options_liquidity_table(files: list[Path], reference: pd.DataFrame | None) -> pd.DataFrame:
    """Por ativo-objeto (índice), média por pregão dos `files` (fechamentos da B3): volume
    financeiro (`turnover_brl`) e nº de negócios (`deals`) das opções; maior volume primeiro."""
    columns = ["turnover_brl", "deals"]
    if not files or reference is None or reference.empty:
        return pd.DataFrame(columns=columns, dtype="float64")
    by_symbol = reference["underlying"]
    roots = pd.Series(by_symbol.to_numpy(), index=by_symbol.index.str[:4])
    by_root = roots.groupby(level=0).agg(lambda s: s.value_counts().index[0])
    totals = []
    for path in files:
        day = pd.read_csv(path, usecols=["symbol", "segment", *columns])
        opts = day[day["segment"].isin(["EQUITY CALL", "EQUITY PUT"])]
        underlying = opts["symbol"].map(by_symbol).fillna(opts["symbol"].str[:4].map(by_root))
        totals.append(opts[columns].groupby(underlying).sum())
    average = pd.concat(totals).groupby(level=0).sum() / len(files)
    return average.sort_values(["turnover_brl", "deals"], ascending=False)


# ---- leitura -----------------------------------------------------------------------------------
def read_snapshot(path: Path) -> pd.DataFrame:
    """Arquivo de snapshot → cadeia com os tipos do app (datas, fusos, nulos)."""
    frame = pd.read_csv(path, compression="gzip", low_memory=False)
    frame["expiration_date"] = pd.to_datetime(frame["expiration_date"]).dt.date
    for col in TIME_COLUMNS:
        frame[col] = pd.to_datetime(frame[col], format="ISO8601", utc=True).dt.tz_convert(
            LOCAL_TIMEZONE
        )
    for col in ("ref_note", "volume_source"):
        frame[col] = frame[col].astype(object).where(frame[col].notna(), None)
    frame["deals"] = frame["deals"].fillna(0).astype("int64")
    return discard_crossed_book(frame)[SNAPSHOT_COLUMNS]


def snapshot_chain(
    frame: pd.DataFrame, underlying: str, today: dt.date, calendar: B3Calendar
) -> tuple[pd.DataFrame, float | None]:
    """Séries vigentes de `underlying` no snapshot, com prazos recalculados para `today`, e o
    preço do ativo lido junto com o lote mais recente."""
    rows = frame[(frame["underlying"] == underlying) & (frame["expiration_date"] >= today)]
    rows = rows.reset_index(drop=True)
    if rows.empty:
        return rows, None
    expirations = pd.Series(rows["expiration_date"].to_numpy())
    rows["dte_business_days"] = calendar.sessions_until(today, expirations).to_numpy()
    rows["dte_calendar_days"] = (
        pd.to_datetime(expirations) - pd.Timestamp(today)
    ).dt.days.to_numpy()
    priced = rows[rows["underlying_price"].notna()]
    spot = (
        float(priced.loc[priced["read_time"].idxmax(), "underlying_price"]) if len(priced) else None
    )
    return rows, spot


@dataclass(frozen=True)
class Snapshot:
    day: dt.date
    slot: str
    captured_at: pd.Timestamp
    status: str
    frame: pd.DataFrame
    note: str | None = None  # ex.: servidor inacessível, usando o último baixado

    @property
    def label(self) -> str:
        return f"{self.captured_at:%d/%m/%Y %H:%M}"


class SnapshotSource:
    """Cliente do servidor de snapshots: índice com cache curto, arquivos baixados uma vez
    (são imutáveis). Servidor inacessível: usa o snapshot mais recente já baixado."""

    def __init__(self, url: str, cache_dir: Path, timeout: float) -> None:
        self._url = url.rstrip("/")
        self._dir = cache_dir
        self._timeout = timeout
        self._lock = threading.Lock()
        self._index: tuple[float, dict] | None = None
        self._failed_at: float | None = None
        self._problem: str | None = None
        self._memo: Snapshot | None = None

    @property
    def problem(self) -> str | None:
        return self._problem

    def _get(self, rel: str) -> bytes:
        with urllib.request.urlopen(f"{self._url}/{rel}", timeout=self._timeout) as resp:  # noqa: S310
            return resp.read()

    def _fetch_index(self) -> dict | None:
        now = time.monotonic()
        if self._index and now - self._index[0] <= INDEX_TTL_SECONDS:
            return self._index[1]
        if self._failed_at is not None and now - self._failed_at < RETRY_AFTER_SECONDS:
            return None
        try:
            index = json.loads(self._get(INDEX_FILE).decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            self._failed_at = now
            self._problem = f"servidor de snapshots inacessível ({self._url}: {exc})"
            log.warning("Snapshots: %s", self._problem)
            return None
        self._failed_at = None
        self._problem = None
        self._index = (now, index)
        return index

    def _local_path(self, day: str, slot: str) -> Path:
        return self._dir / f"{day}_{slot}.csv.gz"

    def _download(self, entry: dict) -> Path:
        path = self._local_path(entry["date"], entry["slot"])
        if not path.exists():
            data = self._get(entry["file"])
            _atomic_write(path, lambda tmp: tmp.write_bytes(data))
            log.info(
                "Snapshot %s %s baixado (%d KB)", entry["date"], entry["slot"], len(data) // 1024
            )
            for old in sorted(self._dir.glob("*.csv.gz"))[:-LOCAL_FILES_KEPT]:
                old.unlink(missing_ok=True)
        return path

    def _load(self, path: Path, status: str, note: str | None) -> Snapshot:
        day, slot = path.name.removesuffix(".csv.gz").split("_")
        if self._memo and (self._memo.day.isoformat(), self._memo.slot) == (day, slot):
            if self._memo.note == note:
                return self._memo
            snap = Snapshot(**{**self._memo.__dict__, "note": note})
        else:
            frame = read_snapshot(path)
            snap = Snapshot(
                dt.date.fromisoformat(day),
                slot,
                frame["captured_at"].min(),
                status,
                frame,
                note,
            )
        self._memo = snap
        return snap

    def latest(self) -> Snapshot | None:
        """Snapshot utilizável mais recente (None se não houver nenhum, nem baixado)."""
        with self._lock:
            index = self._fetch_index()
            if index is not None:
                usable = [
                    e
                    for e in index.get("snapshots", [])
                    if e.get("file") and e.get("status") in USABLE_STATUS
                ]
                if not usable:
                    self._problem = "servidor sem snapshots utilizáveis"
                    return None
                entry = max(usable, key=lambda e: (e["date"], e["slot"]))
                try:
                    path = self._download(entry)
                except (urllib.error.URLError, TimeoutError, OSError) as exc:
                    self._problem = f"falha ao baixar o snapshot {entry['file']}: {exc}"
                    log.warning("Snapshots: %s", self._problem)
                else:
                    return self._load(path, entry["status"], None)
            local = sorted(self._dir.glob("*.csv.gz"))
            if not local:
                return None
            return self._load(
                local[-1],
                "local",
                f"{self._problem}; usando o último snapshot já baixado",
            )
