"""Configuração de logging: console + arquivo com rotação em logs/."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from screener.settings import LoggingSettings, PathSettings

LOG_FILE_NAME = "screener.log"
# O paramiko loga a negociação SSH inteira em INFO; só interessa a partir de WARNING
# (com level DEBUG no YAML, volta a aparecer para diagnosticar a publicação).
QUIET_LIBRARIES = ("paramiko",)
FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
CONSOLE_FORMAT = "%(message)s"


def setup_logging(log_settings: LoggingSettings, paths: PathSettings) -> None:
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(log_settings.level)
    root.handlers.clear()

    file_handler = RotatingFileHandler(
        paths.logs_dir / LOG_FILE_NAME,
        maxBytes=log_settings.max_bytes,
        backupCount=log_settings.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
    root.addHandler(file_handler)

    # Com saída redirecionada no Windows (Agendador de Tarefas, `>` no PowerShell), stdout usa
    # cp1252: acentos funcionam, mas símbolos como "≤" e "−" quebrariam o log. Substitui-os.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    root.addHandler(console)

    if log_settings.level != "DEBUG":
        for name in QUIET_LIBRARIES:
            logging.getLogger(name).setLevel(logging.WARNING)
