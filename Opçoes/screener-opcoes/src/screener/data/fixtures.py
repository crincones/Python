"""Exporta um snapshot real para tests/fixtures/, sem dados da conta nem caminhos locais."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from screener.data.schema import BARS_TABLE, META_FILE, OPTIONS_TABLE, UNDERLYINGS_TABLE

FIXTURE_PREFIX = "snapshot_"
REDACTED = "<removido>"
REDACTED_TERMINAL_KEYS = ("login", "path")


def redact_meta(meta: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(meta))
    terminal = redacted.get("terminal", {})
    for key in REDACTED_TERMINAL_KEYS:
        if key in terminal:
            terminal[key] = REDACTED
    settings = redacted.get("settings", {})
    if "mt5" in settings:
        settings["mt5"]["terminal_path"] = REDACTED
    if "paths" in settings:
        settings["paths"] = {key: REDACTED for key in settings["paths"]}
    return redacted


def export_fixture(snapshot: Path, fixtures_dir: Path) -> Path:
    target = fixtures_dir / f"{FIXTURE_PREFIX}{snapshot.name}"
    if target.exists():
        raise FileExistsError(f"fixture já existe: {target}")
    target.mkdir(parents=True)
    for table in (UNDERLYINGS_TABLE, OPTIONS_TABLE):
        shutil.copy2(snapshot / f"{table}.parquet", target / f"{table}.parquet")
    # Barras só existem em snapshots coletados depois do sinal automático.
    bars = snapshot / f"{BARS_TABLE}.parquet"
    if bars.exists():
        shutil.copy2(bars, target / bars.name)
    meta = json.loads((snapshot / META_FILE).read_text(encoding="utf-8"))
    (target / META_FILE).write_text(
        json.dumps(redact_meta(meta), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target
