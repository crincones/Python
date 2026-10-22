"""Histórico diário da IV ATM (base para um futuro IV Rank/percentil).

Gravado no servidor pelo coletor de snapshots: a cada snapshot (11:00 e 16:30), a IV ATM de cada
ativo e vencimento vai para `<raiz dos snapshots>/iv_atm.csv`, servido pelo mesmo HTTP dos
snapshots. Uma linha por (data, horário, ativo, vencimento); regravar um horário substitui as
linhas dele. `travas iv-history --out <raiz>` refaz o arquivo a partir de todos os snapshots
guardados (os snapshots nunca são apagados no servidor).
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import pandas as pd

from travas.calendar_b3 import B3Calendar
from travas.data.snapshots import _atomic_write, read_snapshot
from travas.options.vol_premium import ATM_COLUMNS, atm_iv_table
from travas.settings import PricingSettings

log = logging.getLogger(__name__)

IV_FILE = "iv_atm.csv"
COLUMNS = ["date", "slot", *ATM_COLUMNS]


def slot_rows(
    frame: pd.DataFrame,
    day: dt.date,
    slot: str,
    rate_annual: float,
    pricing: PricingSettings,
    calendar: B3Calendar,
) -> pd.DataFrame:
    atm = atm_iv_table(frame, rate_annual, pricing, calendar)
    return atm.assign(date=day.isoformat(), slot=slot)[COLUMNS]


def read_history(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path, dtype={"slot": str})


def _write(path: Path, table: pd.DataFrame) -> None:
    table = table.sort_values(["date", "slot", "underlying", "expiration_date"])
    _atomic_write(path, lambda tmp: table.to_csv(tmp, index=False, float_format="%.6f"))


def record(
    root: Path,
    frame: pd.DataFrame,
    day: dt.date,
    slot: str,
    rate_annual: float,
    pricing: PricingSettings,
    calendar: B3Calendar,
) -> int:
    """Grava (ou regrava) as linhas do snapshot `day`/`slot`. Devolve quantas linhas."""
    rows = slot_rows(frame, day, slot, rate_annual, pricing, calendar)
    path = root / IV_FILE
    old = read_history(path)
    old = old[~((old["date"] == day.isoformat()) & (old["slot"] == slot))]
    _write(path, pd.concat([old, rows], ignore_index=True) if len(old) else rows)
    log.info("IV ATM %s %s: %d linhas em %s", day, slot, len(rows), IV_FILE)
    return len(rows)


def rebuild(root: Path, rate_annual: float, pricing: PricingSettings, calendar: B3Calendar) -> int:
    """Refaz o histórico com todos os snapshots guardados em `root`."""
    parts = []
    for path in sorted(root.glob("*/*.csv.gz")):
        day, slot = dt.date.fromisoformat(path.parent.name), path.name.removesuffix(".csv.gz")
        try:
            frame = read_snapshot(path)
        except (OSError, ValueError, KeyError) as exc:
            log.warning("Snapshot ilegível %s: %s", path, exc)
            continue
        parts.append(slot_rows(frame, day, slot, rate_annual, pricing, calendar))
    table = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=COLUMNS)
    _write(root / IV_FILE, table)
    log.info("Histórico de IV ATM refeito: %d linhas de %d snapshots", len(table), len(parts))
    return len(table)
