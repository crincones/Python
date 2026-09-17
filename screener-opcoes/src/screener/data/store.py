"""Leitura e gravação de snapshots (Parquet), com leitura via DuckDB."""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from screener.data.schema import META_FILE
from screener.timeutils import LOCAL_TIMEZONE

log = logging.getLogger(__name__)

SNAPSHOT_NAME_FORMAT = "%Y%m%d_%H%M%S"
SNAPSHOT_NAME_PATTERN = re.compile(r"^\d{8}_\d{6}$")
PARTIAL_SUFFIX = ".partial"
LATEST = "latest"


class SnapshotNotFoundError(FileNotFoundError):
    """Snapshot inexistente ou incompleto."""


def snapshot_name(snapshot_time: pd.Timestamp) -> str:
    return snapshot_time.strftime(SNAPSHOT_NAME_FORMAT)


def write_snapshot(
    snapshots_dir: Path,
    snapshot_time: pd.Timestamp,
    tables: dict[str, pd.DataFrame],
    meta: dict[str, Any],
) -> Path:
    """Grava as tabelas numa pasta temporária e renomeia ao final (snapshot nunca fica pela
    metade com nome válido)."""
    final = snapshots_dir / snapshot_name(snapshot_time)
    if final.exists():
        raise FileExistsError(f"snapshot já existe: {final}")
    partial = final.with_name(final.name + PARTIAL_SUFFIX)
    if partial.exists():
        log.warning("Removendo snapshot parcial anterior: %s", partial)
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    for table, frame in tables.items():
        frame.to_parquet(partial / f"{table}.parquet", index=False)
    (partial / META_FILE).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    partial.rename(final)
    return final


def list_snapshots(snapshots_dir: Path) -> list[Path]:
    if not snapshots_dir.exists():
        return []
    return sorted(
        p for p in snapshots_dir.iterdir() if p.is_dir() and SNAPSHOT_NAME_PATTERN.match(p.name)
    )


def resolve_snapshot(snapshots_dir: Path, name: str) -> Path:
    """`latest` ou o nome AAAAMMDD_HHMMSS de um snapshot completo."""
    if name == LATEST:
        snapshots = list_snapshots(snapshots_dir)
        if not snapshots:
            raise SnapshotNotFoundError(f"nenhum snapshot em {snapshots_dir}")
        return snapshots[-1]
    path = snapshots_dir / name
    if not SNAPSHOT_NAME_PATTERN.match(name) or not (path / META_FILE).exists():
        raise SnapshotNotFoundError(f"snapshot inválido ou incompleto: {path}")
    return path


def read_table(snapshot: Path, table: str) -> pd.DataFrame:
    path = snapshot / f"{table}.parquet"
    if not path.exists():
        raise SnapshotNotFoundError(f"tabela ausente: {path}")
    with duckdb.connect() as con:
        con.execute(f"SET TimeZone = '{LOCAL_TIMEZONE}'")
        return con.execute("SELECT * FROM read_parquet(?)", [str(path)]).df()


def read_meta(snapshot: Path, name: str = META_FILE) -> dict[str, Any]:
    return json.loads((snapshot / name).read_text(encoding="utf-8"))


def write_derived(
    snapshot: Path, tables: dict[str, pd.DataFrame], meta_name: str, meta: dict[str, Any]
) -> None:
    """Grava artefatos derivados (análise) dentro do snapshot, substituindo versões anteriores.

    Cada arquivo é escrito num temporário e depois trocado, para nunca ficar pela metade.
    """
    if not (snapshot / META_FILE).exists():
        raise SnapshotNotFoundError(f"snapshot inválido ou incompleto: {snapshot}")
    for table, frame in tables.items():
        target = snapshot / f"{table}.parquet"
        temporary = target.with_name(target.name + PARTIAL_SUFFIX)
        frame.to_parquet(temporary, index=False)
        temporary.replace(target)
    meta_target = snapshot / meta_name
    meta_temporary = meta_target.with_name(meta_target.name + PARTIAL_SUFFIX)
    meta_temporary.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    meta_temporary.replace(meta_target)
