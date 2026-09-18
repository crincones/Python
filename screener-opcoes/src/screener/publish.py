"""Publicação do relatório HTML no servidor Debian (SSH/SFTP) para acesso pela tailnet.

Único módulo que importa `paramiko`. A lógica de envio é escrita contra o protocolo
`RemoteFiles`, testável offline com um dublê; só o adaptador `_SftpFiles` fala SFTP.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol

import paramiko

from screener.settings import PublishSettings

log = logging.getLogger("screener")

# Sufixo do arquivo temporário: o nome público só passa a apontar para o relatório depois do
# envio completo, para o navegador nunca pegar um HTML pela metade.
PARTIAL_SUFFIX = ".partial"
# Nomes gerados por report.render.REPORT_NAME_FORMAT (ordenam por data alfabeticamente).
REPORT_NAME = re.compile(r"^relatorio_\d{8}_\d{4}\.html$")
BYTES_PER_MB = 1024 * 1024


class PublishError(RuntimeError):
    """Falha de conexão, autenticação, permissão ou envio ao publicar o relatório."""


class RemoteFiles(Protocol):
    """Operações de arquivo usadas no servidor."""

    def makedirs(self, path: str) -> None:
        """Cria o diretório e os pais que faltarem; diretório existente não é erro."""

    def put(self, local: Path, remote: str) -> None:
        """Envia o arquivo local, sobrescrevendo o destino."""

    def listdir(self, path: str) -> list[str]:
        """Nomes (sem caminho) dentro do diretório."""

    def remove(self, path: str) -> None:
        """Apaga o arquivo; arquivo ausente não é erro."""

    def symlink(self, target: str, path: str) -> None:
        """Cria em `path` um link simbólico para `target`."""

    def replace(self, source: str, target: str) -> None:
        """Renomeia `source` para `target`, sobrescrevendo `target` se existir."""


@dataclass(frozen=True)
class PublishResult:
    """Resultado de uma publicação bem-sucedida."""

    url: str
    remote_path: str
    latest_path: str
    size_bytes: int
    removed: tuple[str, ...]
    seconds: float


def obsolete_reports(names: Sequence[str], keep: int) -> list[str]:
    """Relatórios fora dos `keep` mais recentes (o nome do arquivo ordena por data)."""
    reports = sorted(name for name in names if REPORT_NAME.fullmatch(name))
    surplus = len(reports) - max(keep, 1)
    return reports[:surplus] if surplus > 0 else []


def stale_uploads(names: Sequence[str]) -> list[str]:
    """Restos de envios interrompidos."""
    return sorted(name for name in names if name.endswith(PARTIAL_SUFFIX))


def upload_report(remote: RemoteFiles, report: Path, settings: PublishSettings) -> PublishResult:
    """Envia o relatório, aponta o nome público para ele e apaga os mais antigos."""
    started = time.monotonic()
    history = f"{settings.remote_dir}/{settings.history_subdir}"
    remote.makedirs(history)

    final = f"{history}/{report.name}"
    partial = final + PARTIAL_SUFFIX
    remote.put(report, partial)
    remote.replace(partial, final)

    # Nome público = link simbólico relativo para o relatório desta execução, trocado de uma vez.
    latest = f"{settings.remote_dir}/{settings.latest_name}"
    link = latest + PARTIAL_SUFFIX
    remote.remove(link)
    remote.symlink(f"{settings.history_subdir}/{report.name}", link)
    remote.replace(link, latest)

    names = remote.listdir(history)
    removed: list[str] = []
    for name in obsolete_reports(names, settings.keep_reports) + stale_uploads(names):
        if name == report.name:  # nunca apagar o alvo do link recém-criado
            continue
        remote.remove(f"{history}/{name}")
        removed.append(name)

    return PublishResult(
        url=settings.public_url,
        remote_path=final,
        latest_path=latest,
        size_bytes=report.stat().st_size,
        removed=tuple(removed),
        seconds=time.monotonic() - started,
    )


def publish_report(report: Path, settings: PublishSettings) -> PublishResult:
    """Publica o relatório no servidor configurado. Levanta PublishError em qualquer falha."""
    if not report.is_file():
        raise PublishError(f"relatório não encontrado: {report}")
    with _connect(settings) as remote:
        try:
            result = upload_report(remote, report, settings)
        except (OSError, paramiko.SSHException) as exc:
            raise PublishError(f"falha ao enviar {report.name}: {exc}") from exc
    log.info(
        "Relatório publicado em %s (%.1f MB em %.1f s)",
        result.url,
        result.size_bytes / BYTES_PER_MB,
        result.seconds,
    )
    if result.removed:
        log.info(
            "Relatórios antigos removidos do servidor (mantidos %d): %s",
            settings.keep_reports,
            ", ".join(result.removed),
        )
    return result


@contextmanager
def _connect(settings: PublishSettings) -> Iterator[RemoteFiles]:
    """Abre uma sessão SFTP com a host key conferida em known_hosts."""
    client = paramiko.SSHClient()
    known_hosts = settings.known_hosts.expanduser()
    if known_hosts.is_file():
        client.load_system_host_keys(str(known_hosts))
    elif settings.strict_host_key:
        raise PublishError(
            f"known_hosts não encontrado em {known_hosts}: conecte uma vez com "
            f"'ssh {settings.user}@{settings.host}' ou use strict_host_key: false"
        )
    client.set_missing_host_key_policy(
        paramiko.RejectPolicy() if settings.strict_host_key else paramiko.AutoAddPolicy()
    )
    key = settings.private_key.expanduser() if settings.private_key else None
    if key is not None and not key.is_file():
        raise PublishError(f"chave privada não encontrada em {key}")
    timeout = settings.timeout_seconds
    try:
        client.connect(
            hostname=settings.host,
            port=settings.port,
            username=settings.user,
            key_filename=str(key) if key else None,
            look_for_keys=key is None,
            allow_agent=key is None,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
        )
    except (OSError, paramiko.SSHException) as exc:
        client.close()
        raise PublishError(
            f"falha ao conectar em {settings.user}@{settings.host}:{settings.port}: {exc}"
        ) from exc
    try:
        sftp = client.open_sftp()
        sftp.get_channel().settimeout(timeout)
        try:
            yield _SftpFiles(sftp)
        finally:
            sftp.close()
    except (OSError, paramiko.SSHException) as exc:
        raise PublishError(f"falha na sessão SFTP com {settings.host}: {exc}") from exc
    finally:
        client.close()


class _SftpFiles:
    """Adaptador de `RemoteFiles` sobre um SFTPClient do paramiko."""

    def __init__(self, sftp: paramiko.SFTPClient) -> None:
        self._sftp = sftp

    def makedirs(self, path: str) -> None:
        current = ""
        for part in PurePosixPath(path).parts:
            current = part if part == "/" else f"{current.rstrip('/')}/{part}"
            try:
                self._sftp.stat(current)
            except FileNotFoundError:
                self._sftp.mkdir(current)

    def put(self, local: Path, remote: str) -> None:
        self._sftp.put(str(local), remote, confirm=True)

    def listdir(self, path: str) -> list[str]:
        return self._sftp.listdir(path)

    def remove(self, path: str) -> None:
        try:
            self._sftp.remove(path)
        except FileNotFoundError:
            log.debug("nada a apagar em %s", path)

    def symlink(self, target: str, path: str) -> None:
        self._sftp.symlink(target, path)

    def replace(self, source: str, target: str) -> None:
        try:
            self._sftp.posix_rename(source, target)
        except (OSError, paramiko.SSHException) as exc:
            # Servidor sem a extensão posix-rename@openssh.com: apagar e renomear.
            log.debug("posix_rename indisponível (%s); usando remove + rename", exc)
            self.remove(target)
            self._sftp.rename(source, target)
