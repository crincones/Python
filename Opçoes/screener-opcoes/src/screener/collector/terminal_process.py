"""Processo do terminal MT5 no Windows: localizar, abrir (minimizado) e fechar.

Regra de segurança: o screener só fecha terminais que ele mesmo abriu. Um terminal aberto pelo
usuário (gráficos, robôs, serviços) nunca é fechado.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path

log = logging.getLogger(__name__)

PORTABLE_FLAG = "/portable"
SW_SHOWMINNOACTIVE = 7  # janela minimizada, sem roubar o foco
POLL_SECONDS = 1.0
POWERSHELL = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]


def _powershell(script: str) -> str:
    result = subprocess.run(
        [*POWERSHELL, script], capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode != 0:
        raise OSError(f"PowerShell falhou ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def parse_process_list(output: str, executable: Path) -> set[int]:
    """PIDs cujo ExecutablePath é o executável informado (saída JSON do Get-CimInstance)."""
    text = output.strip()
    if not text:
        return set()
    data = json.loads(text)
    items = data if isinstance(data, list) else [data]
    target = str(executable).casefold()
    return {
        int(item["ProcessId"])
        for item in items
        if str(item.get("ExecutablePath") or "").casefold() == target
    }


def running_terminals(executable: Path) -> set[int]:
    output = _powershell(
        "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" | "
        "Select-Object ProcessId, ExecutablePath | ConvertTo-Json -Compress"
    )
    return parse_process_list(output, executable)


def launch_command(executable: Path, portable: bool) -> list[str]:
    return [str(executable), PORTABLE_FLAG] if portable else [str(executable)]


def start_terminal(executable: Path, portable: bool) -> int:
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = SW_SHOWMINNOACTIVE
    process = subprocess.Popen(
        launch_command(executable, portable), cwd=executable.parent, startupinfo=startup
    )
    log.info("Terminal MT5 aberto pelo screener (PID %d): %s", process.pid, executable)
    return process.pid


def close_window_script(ids: str) -> str:
    """Pedido normal de fechamento (equivale a clicar no X da janela)."""
    return (
        f"Get-Process -Id {ids} -ErrorAction SilentlyContinue | "
        "ForEach-Object { [void]$_.CloseMainWindow() }"
    )


def close_terminals(pids: set[int], executable: Path, timeout_seconds: float) -> None:
    """Fecha os PIDs informados: pedido normal de fechamento (salva perfil) e, após o timeout,
    encerramento forçado dos que restarem."""
    alive = pids & running_terminals(executable)
    if not alive:
        return
    ids = ",".join(str(pid) for pid in sorted(alive))
    _powershell(close_window_script(ids))
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        alive &= running_terminals(executable)
        if not alive:
            log.info("Terminal MT5 fechado pelo screener")
            return
        time.sleep(POLL_SECONDS)
    ids = ",".join(str(pid) for pid in sorted(alive))
    log.warning(
        "Terminal MT5 não fechou em %.0f s; encerrando à força (PID %s)", timeout_seconds, ids
    )
    _powershell(f"Stop-Process -Id {ids} -Force -ErrorAction SilentlyContinue")
