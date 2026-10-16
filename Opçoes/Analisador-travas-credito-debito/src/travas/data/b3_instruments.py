"""Ativos-objeto com opções listadas na B3 (arquivo público "InstrumentsConsolidatedFile").

O MT5 da XP só oferece opções de parte dos ativos (48 em 15/10/2026, contra 243 na B3; ex.:
SMAL11, EMBJ3, BPAC11, PETR3 ficam de fora). Esta é a fonte da LISTA COMPLETA de ativos com
opções e da quantidade de séries de cada um; cotações continuam vindo do MT5.

Download: arquivos.b3.com.br/api/download/requestname?fileName=InstrumentsConsolidatedFile&date=
AAAA-MM-DD devolve um token; /api/download/?token=… devolve o CSV (~20 MB, latin-1, ';').
Só um resumo por ativo-objeto é guardado em `data/b3/instrumentos_<data>.csv` (um por dia).
"""

from __future__ import annotations

import datetime as dt
import io
import json
import logging
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar

log = logging.getLogger(__name__)

BASE = "https://arquivos.b3.com.br/api/download"
OPTION_CATEGORIES = ("OPTION ON EQUITIES", "OPTION ON INDEX")
CATEGORY_LABELS = {
    "SHARES": "Ação",
    "UNIT": "Unit",
    "ETF EQUITIES": "ETF",
    "ETF FOREIGN INDEX": "ETF",
    "BDR": "BDR",
    "INDEX": "Índice",
    "FUNDS": "Fundo",
}
SUMMARY_COLUMNS = ["underlying", "b3_series", "calls", "puts", "category", "next_expiration"]
MAX_LOOKBACK_SESSIONS = 5


REFERENCE_COLUMNS = ["symbol", "underlying", "strike", "expiration_date", "exercise_style"]
STYLE_BY_B3 = {"AMER": "american", "EURO": "european"}


def option_reference(raw: pd.DataFrame, as_of: dt.date) -> pd.DataFrame:
    """Dados oficiais de cada opção vigente: ativo-objeto, strike (já ajustado por proventos),
    vencimento e estilo. Referência para corrigir o MT5 de corretoras que trazem `basis` errado
    (Genial: o próprio ticker da opção), strike sem ajuste de provento ou vencimento sem
    considerar feriado (ambos observados na Genial em 15/10/2026)."""
    opts = raw[raw["SctyCtgyNm"].isin(OPTION_CATEGORIES)].copy()
    opts["XprtnDt"] = pd.to_datetime(opts["XprtnDt"], errors="coerce").dt.date
    opts = opts[opts["XprtnDt"] >= as_of]
    strike = pd.to_numeric(
        opts["ExrcPric"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."),
        errors="coerce",
    )
    return pd.DataFrame(
        {
            "symbol": opts["TckrSymb"].to_numpy(),
            "underlying": opts["Asst"].to_numpy(),
            "strike": strike.to_numpy(),
            "expiration_date": opts["XprtnDt"].to_numpy(),
            "exercise_style": opts["OptnStyle"].map(STYLE_BY_B3).to_numpy(),
        }
    )


def summarize(raw: pd.DataFrame, as_of: dt.date) -> pd.DataFrame:
    """CSV da B3 (já lido) → uma linha por ativo-objeto com opções vigentes."""
    opts = raw[raw["SctyCtgyNm"].isin(OPTION_CATEGORIES)].copy()
    opts["XprtnDt"] = pd.to_datetime(opts["XprtnDt"], errors="coerce").dt.date
    opts = opts[opts["XprtnDt"] >= as_of]
    if opts.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    category = raw.drop_duplicates("TckrSymb").set_index("TckrSymb")["SctyCtgyNm"]
    grouped = opts.groupby("Asst")
    out = pd.DataFrame(
        {
            "b3_series": grouped.size(),
            "calls": grouped["OptnTp"].apply(lambda s: int((s == "Call").sum())),
            "puts": grouped["OptnTp"].apply(lambda s: int((s == "Put").sum())),
            "next_expiration": grouped["XprtnDt"].min(),
        }
    )
    out["category"] = [
        CATEGORY_LABELS.get(str(category.get(a, "")), str(category.get(a, "")) or "Outro")
        for a in out.index
    ]
    out = out.rename_axis("underlying").reset_index()
    return out.sort_values("b3_series", ascending=False).reset_index(drop=True)[SUMMARY_COLUMNS]


class B3Instruments:
    def __init__(self, directory: Path, calendar: B3Calendar, timeout: float = 90.0) -> None:
        self._dir = directory
        self._calendar = calendar
        self._timeout = timeout
        self._lock = threading.Lock()
        self._memo: tuple[dt.date, pd.DataFrame] | None = None
        self._map_memo: tuple[dt.date, pd.DataFrame] | None = None

    def _path(self, day: dt.date) -> Path:
        return self._dir / f"instrumentos_{day.isoformat()}.csv"

    def _has_reference(self, day: dt.date) -> bool:
        path = self._map_path(day)
        if not path.exists():
            return False
        header = path.open(encoding="utf-8").readline().strip().split(",")
        return header == REFERENCE_COLUMNS

    def _map_path(self, day: dt.date) -> Path:
        return self._dir / f"opcoes_{day.isoformat()}.csv"

    def reference(self, today: dt.date) -> pd.DataFrame | None:
        """Referência oficial por ticker de opção (índice = symbol), do arquivo do dia."""
        _, day = self.summary(today)
        if day is None or not self._map_path(day).exists():
            return None
        if self._map_memo and self._map_memo[0] == day:
            return self._map_memo[1]
        table = pd.read_csv(self._map_path(day), parse_dates=["expiration_date"])
        table["expiration_date"] = table["expiration_date"].dt.date
        table = table.drop_duplicates("symbol").set_index("symbol")
        self._map_memo = (day, table)
        return table

    def _candidate_days(self, today: dt.date) -> list[dt.date]:
        days = [today] if self._calendar.is_session(today) else []
        return days + list(reversed(self._calendar.previous_sessions(today, MAX_LOOKBACK_SESSIONS)))

    def _download(self, day: dt.date) -> pd.DataFrame | None:
        url = f"{BASE}/requestname?fileName=InstrumentsConsolidatedFile&date={day.isoformat()}"
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
            token = json.loads(resp.read().decode("utf-8")).get("token")
        if not token:
            return None
        with urllib.request.urlopen(f"{BASE}/?token={token}", timeout=self._timeout) as resp:  # noqa: S310
            data = resp.read()
        if len(data) < 1000:  # arquivo ainda não publicado para o dia
            return None
        return pd.read_csv(
            io.BytesIO(data),
            sep=";",
            skiprows=1,  # 1ª linha: "Status do Arquivo: …"
            encoding="latin-1",
            usecols=[
                "TckrSymb",
                "Asst",
                "SctyCtgyNm",
                "XprtnDt",
                "OptnTp",
                "ExrcPric",
                "OptnStyle",
            ],
            low_memory=False,
        )

    def summary(self, today: dt.date) -> tuple[pd.DataFrame | None, dt.date | None]:
        """Resumo mais recente disponível (cache em disco por dia). None se a B3 falhar e não
        houver cache."""
        with self._lock:
            if self._memo and self._memo[0] == today:
                return self._memo[1], self._memo[1].attrs.get("file_date")
            for day in self._candidate_days(today):
                path = self._path(day)
                if path.exists() and self._has_reference(day):
                    table = pd.read_csv(path, parse_dates=["next_expiration"])
                    table["next_expiration"] = table["next_expiration"].dt.date
                    return self._remember(today, table, day)
            for day in self._candidate_days(today):
                try:
                    raw = self._download(day)
                except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                    log.warning("B3: instrumentos de %s indisponíveis: %s", day, exc)
                    continue
                if raw is None:
                    continue
                table = summarize(raw, today)
                self._dir.mkdir(parents=True, exist_ok=True)
                table.to_csv(self._path(day), index=False)
                option_reference(raw, today).to_csv(self._map_path(day), index=False)
                for pattern in ("instrumentos_*.csv", "opcoes_*.csv"):
                    for old in self._dir.glob(pattern):
                        if old not in (self._path(day), self._map_path(day)):
                            old.unlink(missing_ok=True)
                log.info("B3: %d ativos com opções (arquivo de %s)", len(table), day)
                return self._remember(today, table, day)
            # Último recurso: qualquer cache antigo, marcado com a data dele.
            cached = sorted(self._dir.glob("instrumentos_*.csv"))
            if cached:
                day = dt.date.fromisoformat(cached[-1].stem.split("_", 1)[1])
                table = pd.read_csv(cached[-1], parse_dates=["next_expiration"])
                table["next_expiration"] = table["next_expiration"].dt.date
                return self._remember(today, table, day)
            return None, None

    def _remember(self, today: dt.date, table: pd.DataFrame, day: dt.date):
        table.attrs["file_date"] = day
        self._memo = (today, table)
        return table, day
