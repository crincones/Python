"""Persistência local das estruturas acompanhadas (JSON, gravação atômica).

Arquivo em `data/acompanhamento.json` (fora do git). Uma cópia `.bak` da versão anterior é
mantida a cada gravação. Nenhuma credencial é armazenada.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import threading
import uuid
from pathlib import Path

SCHEMA_VERSION = 1


class TrackingStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if not self._path.exists():
            return {"version": SCHEMA_VERSION, "positions": []}
        data = json.loads(self._path.read_text(encoding="utf-8"))
        data.setdefault("positions", [])
        return data

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), "utf-8")
        if self._path.exists():
            os.replace(self._path, self._path.with_suffix(".bak"))
        os.replace(tmp, self._path)

    def list(self) -> list[dict]:
        with self._lock:
            return self._read()["positions"]

    def get(self, position_id: str) -> dict | None:
        return next((p for p in self.list() if p["id"] == position_id), None)

    def add(self, position: dict) -> dict:
        with self._lock:
            data = self._read()
            now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
            record = {
                **position,
                "id": uuid.uuid4().hex[:10],
                "created_at": now,
                "status": "aberta",
            }
            data["positions"].append(record)
            self._write(data)
            return record

    def update(self, position_id: str, changes: dict) -> dict:
        with self._lock:
            data = self._read()
            for i, p in enumerate(data["positions"]):
                if p["id"] == position_id:
                    data["positions"][i] = {**p, **changes, "id": position_id}
                    self._write(data)
                    return data["positions"][i]
        raise KeyError(position_id)

    def delete(self, position_id: str) -> None:
        with self._lock:
            data = self._read()
            kept = [p for p in data["positions"] if p["id"] != position_id]
            if len(kept) == len(data["positions"]):
                raise KeyError(position_id)
            data["positions"] = kept
            self._write(data)
