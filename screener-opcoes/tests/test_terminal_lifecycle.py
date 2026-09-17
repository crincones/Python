"""Ciclo de vida do terminal MT5 com processo e API simulados (sem abrir nem fechar nada)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from screener.collector import mt5_client, terminal_process
from screener.collector.mt5_client import MT5Client, MT5Error
from screener.settings import load_settings

EXE = Path(r"C:\MT5\terminal64.exe")


def _settings(**overrides: object):
    base = load_settings().mt5.model_copy(
        update={
            "terminal_path": EXE,
            "startup_timeout_seconds": 1.0,
            "startup_stable_seconds": 0.0,
            "quote_poll_seconds": 0.01,
            "retry_wait_seconds": 0.0,
            "init_retries": 1,
        }
    )
    return base.model_copy(update=overrides)


class FakeWorld:
    """Processos terminal64 e API MT5 falsos."""

    def __init__(self, running: set[int], ready: bool = True, init_ok: bool = True) -> None:
        self.running = set(running)
        self.ready = ready
        self.init_ok = init_ok
        self.started: list[bool] = []
        self.closed: list[set[int]] = []
        self.init_kwargs: dict = {}

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        tp = terminal_process
        monkeypatch.setattr(tp, "running_terminals", lambda exe: set(self.running))
        monkeypatch.setattr(tp, "start_terminal", self._start)
        monkeypatch.setattr(tp, "close_terminals", self._close)
        fake_mt5 = SimpleNamespace(
            initialize=self._initialize,
            shutdown=lambda: None,
            last_error=lambda: (1, "ok"),
            terminal_info=lambda: SimpleNamespace(connected=self.ready),
            account_info=lambda: SimpleNamespace(login=123) if self.ready else None,
            symbols_total=lambda: 57216 if self.ready else 0,
        )
        monkeypatch.setattr(mt5_client, "mt5", fake_mt5)

    def _initialize(self, **kwargs: object) -> bool:
        self.init_kwargs = kwargs
        return self.init_ok

    def _start(self, exe: Path, portable: bool) -> int:
        self.started.append(portable)
        self.running.add(999)
        return 999

    def _close(self, pids: set[int], exe: Path, timeout: float) -> None:
        self.closed.append(set(pids))
        self.running -= pids


def test_terminal_already_open_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    world = FakeWorld(running={3264})
    world.install(monkeypatch)
    with MT5Client(_settings()):
        pass
    assert world.started == []
    assert world.closed == []
    assert world.running == {3264}


def test_closed_terminal_is_opened_portable_and_closed_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = FakeWorld(running=set())
    world.install(monkeypatch)
    with MT5Client(_settings()):
        assert world.running == {999}
    assert world.started == [True]
    assert world.closed == [{999}]
    assert world.init_kwargs["portable"] is True
    assert world.init_kwargs["timeout"] == 1000


def test_launched_terminal_is_closed_even_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    world = FakeWorld(running=set())
    world.install(monkeypatch)
    with pytest.raises(RuntimeError), MT5Client(_settings()):
        raise RuntimeError("falha na coleta")
    assert world.closed == [{999}]


def test_launched_terminal_is_closed_when_it_never_gets_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = FakeWorld(running=set(), ready=False)
    world.install(monkeypatch)
    with pytest.raises(MT5Error, match="não ficou pronto"), MT5Client(_settings()):
        pytest.fail("não deveria entrar no bloco")
    assert world.closed == [{999}]


def test_keep_launched_terminal_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    world = FakeWorld(running=set())
    world.install(monkeypatch)
    with MT5Client(_settings(close_if_launched=False)):
        pass
    assert world.started == [True]
    assert world.closed == []


def test_no_launch_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    world = FakeWorld(running=set(), init_ok=False)
    world.install(monkeypatch)
    with pytest.raises(MT5Error), MT5Client(_settings(launch_if_closed=False)):
        pass
    assert world.started == []


def test_only_processes_opened_by_screener_are_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    # Terminal reiniciado por atualização durante a execução: PID novo também é do screener.
    world = FakeWorld(running=set())
    world.install(monkeypatch)
    with MT5Client(_settings()):
        world.running = {1234}
    assert world.closed == [{1234}]


def test_parse_process_list_matches_exact_executable() -> None:
    output = json.dumps(
        [
            {"ProcessId": 10, "ExecutablePath": r"C:\MT5\terminal64.exe"},
            {"ProcessId": 11, "ExecutablePath": r"C:\Outro\terminal64.exe"},
            {"ProcessId": 12, "ExecutablePath": None},
        ]
    )
    assert terminal_process.parse_process_list(output, EXE) == {10}
    single = json.dumps({"ProcessId": 7, "ExecutablePath": r"c:\mt5\TERMINAL64.EXE"})
    assert terminal_process.parse_process_list(single, EXE) == {7}
    assert terminal_process.parse_process_list("", EXE) == set()


def test_launch_command_and_close_script() -> None:
    assert terminal_process.launch_command(EXE, True) == [str(EXE), "/portable"]
    assert terminal_process.launch_command(EXE, False) == [str(EXE)]
    script = terminal_process.close_window_script("10,11")
    assert "{ [void]$_.CloseMainWindow() }" in script
    assert "{{" not in script
