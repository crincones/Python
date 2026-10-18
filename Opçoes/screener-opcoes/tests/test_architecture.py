from __future__ import annotations

import re

from screener.settings import PROJECT_ROOT

SRC = PROJECT_ROOT / "src" / "screener"
COLLECTOR = SRC / "collector"
PUBLISH = SRC / "publish.py"
MT5_IMPORT = re.compile(r"^\s*(import|from)\s+MetaTrader5\b", re.MULTILINE)
PARAMIKO_IMPORT = re.compile(r"^\s*(import|from)\s+paramiko\b", re.MULTILINE)
TRADING_CALLS = re.compile(r"\border_(send|check)\b|\bpositions?_|\bhistory_orders")


def test_metatrader5_is_imported_only_in_collector() -> None:
    offenders = [
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if COLLECTOR not in path.parents and MT5_IMPORT.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_paramiko_is_imported_only_in_publish() -> None:
    offenders = [
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if path != PUBLISH and PARAMIKO_IMPORT.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_no_trading_functions_are_used() -> None:
    offenders = [
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if TRADING_CALLS.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
