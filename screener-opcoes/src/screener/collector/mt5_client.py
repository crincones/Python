"""Conexão com o terminal MetaTrader 5. Somente leitura: nenhuma função de trading é usada."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any, Self

import MetaTrader5 as mt5
import pandas as pd

from screener.collector import terminal_process
from screener.settings import MT5Settings

log = logging.getLogger(__name__)

MS_PER_SECOND = 1000


class MT5Error(RuntimeError):
    """Falha de chamada à API do MetaTrader 5."""


def _fail(call: str) -> MT5Error:
    error = mt5.last_error()
    log.error("MT5: %s falhou: %s", call, error)
    return MT5Error(f"{call} falhou: {error}")


class MT5Client:
    """Uma conexão por processo. A API do MT5 não é thread-safe.

    Como gerenciador de contexto: se o terminal estiver fechado (e `launch_if_closed`), abre-o
    minimizado, espera login e sincronização e, ao sair, fecha só o que ele mesmo abriu
    (`close_if_launched`). Terminal já aberto pelo usuário é mantido.
    """

    def __init__(self, settings: MT5Settings) -> None:
        self._settings = settings
        self._launched = False
        self._preexisting: set[int] = set()

    def __enter__(self) -> Self:
        self._ensure_terminal_running()
        try:
            self.connect()
            self._wait_until_ready()
        except BaseException:
            self.close()
            self._release_terminal()
            raise
        return self

    def __exit__(self, *exc_info: object) -> None:
        try:
            self.close()
        finally:
            self._release_terminal()

    def _ensure_terminal_running(self) -> None:
        s = self._settings
        if not s.launch_if_closed:
            return
        self._preexisting = terminal_process.running_terminals(s.terminal_path)
        if self._preexisting:
            log.info(
                "Terminal MT5 já aberto (PID %s): será mantido aberto",
                ", ".join(map(str, sorted(self._preexisting))),
            )
            return
        terminal_process.start_terminal(s.terminal_path, s.portable)
        self._launched = True

    def _release_terminal(self) -> None:
        s = self._settings
        if not (self._launched and s.close_if_launched):
            return
        # Diferença de conjuntos: cobre reinício do terminal por atualização (PID novo).
        opened = terminal_process.running_terminals(s.terminal_path) - self._preexisting
        terminal_process.close_terminals(opened, s.terminal_path, s.shutdown_timeout_seconds)
        self._launched = False

    def _wait_until_ready(self) -> None:
        """Espera conexão com o servidor, conta carregada e lista de símbolos estável."""
        s = self._settings
        deadline = time.monotonic() + s.startup_timeout_seconds
        last_total, stable_since = -1, time.monotonic()
        while time.monotonic() < deadline:
            terminal, account = mt5.terminal_info(), mt5.account_info()
            total = mt5.symbols_total() if terminal is not None else 0
            if total != last_total:
                last_total, stable_since = total, time.monotonic()
            connected = terminal is not None and terminal.connected and account is not None
            if (
                connected
                and total > 0
                and time.monotonic() - stable_since >= s.startup_stable_seconds
            ):
                log.info("Terminal pronto: conta %s, %d símbolos", account.login, total)
                return
            time.sleep(s.quote_poll_seconds)
        raise MT5Error(
            f"terminal não ficou pronto em {s.startup_timeout_seconds:.0f} s "
            f"(conectado/logado/símbolos estáveis); último erro: {mt5.last_error()}"
        )

    def connect(self) -> None:
        s = self._settings
        path = str(s.terminal_path)
        timeout_ms = int(s.startup_timeout_seconds * MS_PER_SECOND)
        for attempt in range(1, s.init_retries + 1):
            if mt5.initialize(path=path, portable=s.portable, timeout=timeout_ms):
                log.info("MT5 conectado (tentativa %d): %s", attempt, path)
                return
            log.warning("MT5 initialize falhou (tentativa %d): %s", attempt, mt5.last_error())
            mt5.shutdown()
            time.sleep(s.retry_wait_seconds)
        raise _fail(f"initialize({path})")

    def close(self) -> None:
        mt5.shutdown()
        log.info("MT5 desconectado")

    def terminal_summary(self) -> dict[str, Any]:
        terminal = mt5.terminal_info()
        if terminal is None:
            raise _fail("terminal_info")
        account = mt5.account_info()
        if account is None:
            raise _fail("account_info")
        return {
            "build": terminal.build,
            "connected": terminal.connected,
            "path": terminal.path,
            "login": account.login,
            "server": account.server,
            "company": account.company,
        }

    def symbols(self, group: str | None = None) -> pd.DataFrame:
        """Todos os símbolos do servidor (sem cotações confiáveis se não selecionados)."""
        for attempt in range(1, self._settings.init_retries + 1):
            result = mt5.symbols_get(group=group) if group else mt5.symbols_get()
            if result is not None:
                return pd.DataFrame([s._asdict() for s in result])
            log.warning("MT5 symbols_get falhou (tentativa %d): %s", attempt, mt5.last_error())
            time.sleep(self._settings.retry_wait_seconds)
        raise _fail(f"symbols_get({group!r})")

    def symbol_infos(self, names: list[str]) -> pd.DataFrame:
        rows = []
        for name in names:
            info = mt5.symbol_info(name)
            if info is None:
                log.warning("MT5: symbol_info(%s) falhou: %s", name, mt5.last_error())
                continue
            rows.append(info._asdict())
        return pd.DataFrame(rows)

    def selected_batches(
        self, names: list[str], heartbeat: str | None = None
    ) -> Iterator[list[str]]:
        """Seleciona os símbolos no Market Watch em lotes, aguarda as cotações e devolve cada lote.

        `heartbeat`: símbolo líquido já selecionado (ex.: o ativo-objeto). O lote só é liberado
        depois que o tick dele avança além do instante do select, sinal de que o terminal
        processou a fila de cotações (medido na XP: o terminal inteiro congela por alguns
        segundos após muitas assinaturas seguidas).

        Ao avançar para o próximo lote, desmarca os símbolos que não estavam selecionados antes,
        preservando o Market Watch do usuário.
        """
        size = self._settings.select_batch_size
        for start in range(0, len(names), size):
            batch = names[start : start + size]
            before = self._tick_msc(heartbeat) if heartbeat else None
            added = [name for name in batch if self._select(name)]
            self._wait_for_quotes(batch, heartbeat, before)
            try:
                yield [name for name in batch if self._is_selected(name)]
            finally:
                for name in added:
                    if not mt5.symbol_select(name, False):
                        log.warning(
                            "MT5: symbol_select(%s, False) falhou: %s", name, mt5.last_error()
                        )

    def _wait_for_quotes(
        self, batch: list[str], heartbeat: str | None, heartbeat_before: int | None
    ) -> None:
        """Espera as cotações chegarem: sai quando o heartbeat avançou e o número de séries com
        tick parou de crescer (após o tempo mínimo), ou no timeout."""
        s = self._settings
        start = time.monotonic()
        previous = -1
        while True:
            time.sleep(s.quote_poll_seconds)
            quoted = sum(1 for name in batch if (i := mt5.symbol_info(name)) and i.time > 0)
            alive = heartbeat is None or self._tick_msc(heartbeat) > (heartbeat_before or 0)
            elapsed = time.monotonic() - start
            if elapsed >= s.quote_wait_timeout_seconds:
                log.debug(
                    "Timeout aguardando cotações: %d/%d com tick, heartbeat %s avançou=%s",
                    quoted,
                    len(batch),
                    heartbeat,
                    alive,
                )
                return
            if alive and quoted == previous and elapsed >= s.quote_min_wait_seconds:
                return
            previous = quoted

    def _tick_msc(self, name: str) -> int:
        tick = mt5.symbol_info_tick(name)
        return tick.time_msc if tick is not None else 0

    def cool_down(self) -> None:
        """Pausa para o terminal esvaziar a fila de cotações. Reconecta se tiver caído."""
        time.sleep(self._settings.feed_cooldown_seconds)
        terminal = mt5.terminal_info()
        if terminal is None or not terminal.connected:
            log.warning("Terminal desconectado do servidor; reconectando a API")
            self.close()
            self.connect()

    def _is_selected(self, name: str) -> bool:
        info = mt5.symbol_info(name)
        return info is not None and info.select

    def _select(self, name: str) -> bool:
        """Seleciona o símbolo. Retorna True se ele não estava selecionado antes."""
        if self._is_selected(name):
            return False
        if not mt5.symbol_select(name, True):
            log.warning("MT5: symbol_select(%s, True) falhou: %s", name, mt5.last_error())
            return False
        return True

    def daily_rates(self, name: str, count: int) -> pd.DataFrame:
        return self.rates(name, "d1", count)

    def rates(self, name: str, timeframe: str, count: int) -> pd.DataFrame:
        rates = mt5.copy_rates_from_pos(name, TIMEFRAMES[timeframe], 0, count)
        if rates is None:
            raise _fail(f"copy_rates_from_pos({name}, {timeframe}, 0, {count})")
        return pd.DataFrame(rates)


TIMEFRAMES = {"d1": mt5.TIMEFRAME_D1, "h4": mt5.TIMEFRAME_H4}

OPTION_RIGHT_NAMES = {
    mt5.SYMBOL_OPTION_RIGHT_CALL: "call",
    mt5.SYMBOL_OPTION_RIGHT_PUT: "put",
}
OPTION_MODE_NAMES = {
    mt5.SYMBOL_OPTION_MODE_EUROPEAN: "european",
    mt5.SYMBOL_OPTION_MODE_AMERICAN: "american",
}
