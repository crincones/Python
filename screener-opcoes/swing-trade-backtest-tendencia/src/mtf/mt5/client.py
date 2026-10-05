"""Conexão com o MetaTrader 5. ÚNICO módulo (com download.py) que importa MetaTrader5.

Somente leitura: nenhuma função de trading é usada.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Self

import MetaTrader5 as mt5
import pandas as pd

from mtf.config import MT5Settings
from mtf.mt5 import terminal

log = logging.getLogger(__name__)

MT5_TIMEFRAMES = {"D1": mt5.TIMEFRAME_D1, "H4": mt5.TIMEFRAME_H4, "H1": mt5.TIMEFRAME_H1}


class MT5Error(RuntimeError):
    """Falha de chamada à API do MetaTrader 5."""


def _fail(call: str) -> MT5Error:
    error = mt5.last_error()
    log.error("MT5: %s falhou: %s", call, error)
    return MT5Error(f"{call} falhou: {error}")


class MT5Client:
    """Uma conexão por processo (a API não é thread-safe).

    Como contexto: abre o terminal minimizado se estiver fechado e, ao sair, fecha só os
    processos que ele mesmo abriu.
    """

    def __init__(self, settings: MT5Settings) -> None:
        self._settings = settings
        self._launched = False
        self._preexisting: set[int] = set()

    def __enter__(self) -> Self:
        s = self._settings
        if s.launch_if_closed:
            self._preexisting = terminal.running_terminals(s.terminal_path)
            if not self._preexisting:
                terminal.start_terminal(s.terminal_path, s.portable)
                self._launched = True
        try:
            self._connect()
            self._wait_until_ready()
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *exc_info: object) -> None:
        mt5.shutdown()
        s = self._settings
        if self._launched and s.close_if_launched:
            opened = terminal.running_terminals(s.terminal_path) - self._preexisting
            terminal.close_terminals(opened, s.terminal_path, s.shutdown_timeout_seconds)
            self._launched = False

    def _connect(self) -> None:
        s = self._settings
        timeout_ms = int(s.startup_timeout_seconds * 1000)
        for attempt in range(1, s.init_retries + 1):
            if mt5.initialize(path=str(s.terminal_path), portable=s.portable, timeout=timeout_ms):
                return
            log.warning("MT5 initialize falhou (tentativa %d): %s", attempt, mt5.last_error())
            mt5.shutdown()
            time.sleep(s.retry_wait_seconds)
        raise _fail(f"initialize({s.terminal_path})")

    def _wait_until_ready(self) -> None:
        s = self._settings
        deadline = time.monotonic() + s.startup_timeout_seconds
        last_total, stable_since = -1, time.monotonic()
        while time.monotonic() < deadline:
            info, account = mt5.terminal_info(), mt5.account_info()
            total = mt5.symbols_total() if info is not None else 0
            if total != last_total:
                last_total, stable_since = total, time.monotonic()
            ready = info is not None and info.connected and account is not None and total > 0
            if ready and time.monotonic() - stable_since >= s.startup_stable_seconds:
                log.info("Terminal pronto: build %s, %d símbolos", info.build, total)
                return
            time.sleep(0.5)
        raise MT5Error(f"terminal não ficou pronto em {s.startup_timeout_seconds:.0f} s")

    def terminal_build(self) -> int:
        info = mt5.terminal_info()
        if info is None:
            raise _fail("terminal_info")
        return int(info.build)

    def symbols(self) -> pd.DataFrame:
        result = mt5.symbols_get()
        if result is None:
            raise _fail("symbols_get()")
        return pd.DataFrame([s._asdict() for s in result])

    def select(self, symbol: str) -> None:
        if not mt5.symbol_select(symbol, True):
            raise _fail(f"symbol_select({symbol})")

    def rates_range(
        self, symbol: str, timeframe: str, start: dt.datetime, end: dt.datetime
    ) -> pd.DataFrame:
        """Barras no intervalo. Repete enquanto o histórico ainda está sincronizando (a
        contagem muda entre chamadas)."""
        s = self._settings
        previous = -1
        frame = pd.DataFrame()
        for _attempt in range(s.history_retries):
            rates = mt5.copy_rates_range(symbol, MT5_TIMEFRAMES[timeframe], start, end)
            if rates is None:
                raise _fail(f"copy_rates_range({symbol}, {timeframe})")
            frame = pd.DataFrame(rates)
            if len(frame) == previous:
                return frame
            previous = len(frame)
            time.sleep(s.retry_wait_seconds)
        log.info(
            "%s %s: contagem de barras não estabilizou; usando %d", symbol, timeframe, previous
        )
        return frame
