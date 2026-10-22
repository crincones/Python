"""Ranking dos ativos pela liquidez das opções (aba "Liquidez de Opções").

Liquidez = volume financeiro médio por pregão somando todas as séries (calls e puts) do
ativo-objeto, nos últimos N pregões do fechamento oficial da B3 ("TradeInformationConsolidated
File", o mesmo de `b3_trades`). Mesma metodologia do script `lista-opcoes-profitchart` e da
escolha dos ativos do coletor de snapshots.

Os arquivos de cada pregão ficam em `data/b3/negocios/<data>/negocios_b3.csv` (cache por dia; a
B3 publica o do dia à noite). Ativo de cada opção pela referência oficial de instrumentos;
séries já vencidas pela raiz do ticker.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
import threading
import time
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.b3_instruments import B3Instruments
from travas.data.b3_trades import B3Trades
from travas.data.snapshots import B3_FILE, options_liquidity_table

log = logging.getLogger(__name__)

MAX_SESSIONS = 20
ATM_BAND = 0.10  # "perto do dinheiro": strike a até ±10% do spot
SORT_KEYS = {
    "rank": ("rank", False),
    "ticker": ("underlying", False),
    "turnover": ("turnover_brl", True),
    "deals": ("deals", True),
    "series": ("b3_series", True),
    "book": ("book_spread", False),  # spread mediano: menor é melhor
    "mt5": ("has_mt5_options", True),
    "ivhv": ("ivhv", False),  # IV/HV do 1º vencimento mensal: menor = opções mais baratas
}
IVHV_CSV_EXPIRATIONS = 3
LOOKBACK_EXTRA = 5  # pregões a mais para pular dias ainda não publicados
RETRY_MISSING_SECONDS = 15 * 60
FILES_KEPT = 40


class OptionsLiquidity:
    def __init__(self, directory: Path, calendar: B3Calendar, instruments: B3Instruments) -> None:
        self._dir = directory
        self._calendar = calendar
        self._instruments = instruments
        self._trades = B3Trades(directory / "_tmp", calendar)
        self._lock = threading.Lock()
        self._missing: dict[dt.date, float] = {}
        self._progress: dict = {"active": False}

    def progress(self) -> dict:
        """Etapa da montagem em andamento (a tela consulta enquanto espera)."""
        return dict(self._progress)

    def _report(self, **state) -> None:
        self._progress = {"active": True, **state}

    def _path(self, day: dt.date) -> Path:
        return self._dir / day.isoformat() / B3_FILE

    def _ensure(self, day: dt.date) -> bool:
        path = self._path(day)
        if path.exists():
            return True
        tried = self._missing.get(day)
        if tried is not None and time.monotonic() - tried < RETRY_MISSING_SECONDS:
            return False
        table = self._trades.fetch(day)
        if table is None:
            self._missing[day] = time.monotonic()
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        table.to_csv(tmp)
        tmp.replace(path)
        log.info("B3: negócios de %s guardados para a liquidez das opções", day)
        return True

    def _prune(self) -> None:
        for old in sorted(self._dir.glob(f"*/{B3_FILE}"))[:-FILES_KEPT]:
            old.unlink(missing_ok=True)

    def ranking(self, today: dt.date, sessions: int) -> dict:
        """Tabela completa (todos os ativos com negócio em opções no período) e os pregões."""
        sessions = max(1, min(sessions, MAX_SESSIONS))
        candidates = ([today] if self._calendar.is_session(today) else []) + list(
            reversed(self._calendar.previous_sessions(today, sessions + LOOKBACK_EXTRA))
        )
        with self._lock:
            try:
                days = []
                for day in candidates:
                    if len(days) == sessions:
                        break
                    cached = self._path(day).exists()
                    self._report(
                        phase="lendo" if cached else "baixando",
                        day=day.isoformat(),
                        done=len(days),
                        total=sessions,
                    )
                    if self._ensure(day):
                        days.append(day)
                self._prune()
                days.sort()
                self._report(phase="cadastro", done=len(days), total=sessions)
                reference = self._instruments.reference(today)
                summary, _ = self._instruments.summary(today)
                self._report(phase="calculando", done=len(days), total=sessions)
                table = options_liquidity_table([self._path(d) for d in days], reference)
            finally:
                self._progress = {"active": False}
        info = (
            summary.set_index("underlying")[["b3_series", "category"]]
            if summary is not None and not summary.empty
            else pd.DataFrame(columns=["b3_series", "category"])
        )
        rows = []
        for position, (underlying, values) in enumerate(table.iterrows(), start=1):
            meta = info.loc[underlying] if underlying in info.index else None
            rows.append(
                {
                    "rank": position,
                    "underlying": str(underlying),
                    "turnover_brl": float(values["turnover_brl"]),
                    "deals": float(values["deals"]),
                    "b3_series": int(meta["b3_series"]) if meta is not None else None,
                    "category": meta["category"] if meta is not None else None,
                }
            )
        return {
            "sessions_requested": sessions,
            "sessions": [d.isoformat() for d in days],
            "rows": rows,
            "missing_reference": reference is None,
        }


def book_quality(frame: pd.DataFrame, min_mid: float, band: float = ATM_BAND) -> dict[str, dict]:
    """Qualidade do book por ativo num snapshot: séries com strike a até ±`band` do spot e
    mid ≥ `min_mid`; quantas têm bid e ask válidos e o spread mediano (ask − bid)/mid delas."""
    out: dict[str, dict] = {}
    for underlying, rows in frame.groupby("underlying"):
        priced = rows[rows["underlying_price"].notna()]
        if priced.empty:
            continue
        spot = float(priced.loc[priced["read_time"].idxmax(), "underlying_price"])
        near = rows[(rows["strike"] / spot - 1).abs() <= band]
        cheap = near["mid"].notna() & (near["mid"] < min_mid)
        near = near[~cheap]
        booked = near[near["mid"].notna()]
        out[str(underlying)] = {
            "book_series": int(len(near)),
            "book_with_quotes": int(len(booked)),
            "book_spread": float(booked["spread_pct_mid"].median()) if len(booked) else None,
        }
    return out


def sort_rows(rows: list[dict], key: str, desc: bool | None = None) -> list[dict]:
    """Ordena pela coluna pedida (sentido padrão da coluna, ou o informado); vazios no fim."""
    field, default_desc = SORT_KEYS.get(key, SORT_KEYS["rank"])
    desc = default_desc if desc is None else desc
    present = [r for r in rows if r.get(field) is not None]
    missing = [r for r in rows if r.get(field) is None]
    present.sort(key=lambda r: r[field], reverse=desc)
    return present + missing


def ranking_csv(result: dict, rows: list[dict]) -> str:
    """CSV no padrão do Excel pt-BR (; e vírgula decimal), com BOM."""
    out = io.StringIO()
    out.write("﻿")
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n")
    writer.writerow(
        [
            "posicao",
            "ticker",
            "categoria",
            "giro_medio_opcoes_rs_dia",
            "negocios_medios_opcoes_dia",
            "series_vigentes_b3",
            "opcoes_no_mt5",
            "spread_mediano_atm_pct",
            "series_atm_com_book",
            "series_atm",
            "iv_hv_classificacao",
            "iv_hv_pouco_confiavel",
            *(
                f"{name}_m{i}"
                for i in range(1, IVHV_CSV_EXPIRATIONS + 1)
                for name in ("vencimento", "iv_atm_pct", "hv_pct", "iv_hv")
            ),
        ]
    )
    for r in rows:
        mt5 = r.get("has_mt5_options")
        spread = r.get("book_spread")
        writer.writerow(
            [
                r["rank"],
                r["underlying"],
                r.get("category") or "",
                f"{r['turnover_brl']:.0f}",
                f"{r['deals']:.0f}",
                "" if r.get("b3_series") is None else r["b3_series"],
                "" if mt5 is None else ("sim" if mt5 else "não"),
                "" if spread is None else f"{100 * spread:.1f}".replace(".", ","),
                "" if r.get("book_with_quotes") is None else r["book_with_quotes"],
                "" if r.get("book_series") is None else r["book_series"],
                r.get("ivhv_label") or "",
                r.get("ivhv_weak") or "",
                *_ivhv_cells(r.get("ivhv_items") or []),
            ]
        )
    return out.getvalue()


def _dec(value: float | None, digits: int, scale: float = 1.0) -> str:
    return "" if value is None else f"{scale * value:.{digits}f}".replace(".", ",")


def _ivhv_cells(items: list[dict]) -> list[str]:
    cells: list[str] = []
    for i in range(IVHV_CSV_EXPIRATIONS):
        it = items[i] if i < len(items) else {}
        cells += [
            it.get("expiration", ""),
            _dec(it.get("atm_iv"), 1, 100),
            _dec(it.get("hv"), 1, 100),
            _dec(it.get("ratio"), 2),
        ]
    return cells


def csv_filename(result: dict, top: int) -> str:
    days = result["sessions"]
    period = f"{days[0]}_a_{days[-1]}" if days else "sem_dados"
    size = f"top{top}" if top else "todos"
    return f"liquidez_opcoes_{size}_{len(days)}pregoes_{period}.csv"
