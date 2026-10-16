"""Ativos marcados com estrela ("seguimento"), para observar padrões de entrada.

Arquivo `data/favoritos.json` (fora do git), gravação atômica com cópia `.bak`. Guarda só o
ticker, quando foi marcado e o preço exibido no momento (se houver); nenhuma credencial.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import threading
from pathlib import Path

from travas.data.normalize import UNDERLYING_TICKER_RE

SCHEMA_VERSION = 1
NOTE_MAX = 200


class WatchlistError(ValueError):
    pass


def normalize_ticker(ticker: str) -> str:
    t = (ticker or "").strip().upper()
    if not re.fullmatch(UNDERLYING_TICKER_RE, t):
        raise WatchlistError(f"ticker inválido: {ticker!r}")
    return t


class WatchlistStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if not self._path.exists():
            return {"version": SCHEMA_VERSION, "items": []}
        data = json.loads(self._path.read_text(encoding="utf-8"))
        data.setdefault("items", [])
        return data

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        if self._path.exists():
            os.replace(self._path, self._path.with_suffix(".bak"))
        os.replace(tmp, self._path)

    def list(self) -> list[dict]:
        with self._lock:
            return self._read()["items"]

    def add(self, ticker: str, price: float | None = None, note: str | None = None) -> dict:
        t = normalize_ticker(ticker)
        if price is not None and not (price > 0):
            raise WatchlistError("preço inválido")
        with self._lock:
            data = self._read()
            for item in data["items"]:
                if item["ticker"] == t:
                    if note is not None:
                        item["note"] = note[:NOTE_MAX]
                        self._write(data)
                    return item
            item = {
                "ticker": t,
                "added_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "price_at_add": price,
                "note": (note or "")[:NOTE_MAX],
            }
            data["items"].append(item)
            self._write(data)
            return item

    def remove(self, ticker: str) -> bool:
        t = normalize_ticker(ticker)
        with self._lock:
            data = self._read()
            kept = [i for i in data["items"] if i["ticker"] != t]
            if len(kept) == len(data["items"]):
                return False
            data["items"] = kept
            self._write(data)
            return True
