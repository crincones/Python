"""Cópia da Carteira (estruturas abertas e encerradas) e dos favoritos no Google Drive.

- Permissão mínima: escopo `drive.file` — o app só enxerga os arquivos que ele mesmo criou
  (a pasta "Dash CIRP – Carteira" e o que está dentro); o resto do Drive fica fora do alcance.
- Usa a mesma conexão Google do Agenda/e-mail (`CalendarSync`): um só refresh token, cifrado
  pela DPAPI. Aqui só ficam os ids da pasta/arquivos e o hash do último envio
  (`data/google_drive.json`, sem credenciais).
- O arquivo local continua sendo a fonte da verdade; o Drive recebe uma cópia a cada mudança
  (com alguns segundos de espera para juntar gravações seguidas) e a cada `sync_minutes`.
  Na pasta: a versão atual de cada arquivo (o Drive guarda as revisões anteriores) e, em
  "Histórico", uma cópia por dia (`acompanhamento_AAAA-MM-DD.json`, a última do dia).
- Só envia quando o conteúdo mudou (sha256). Nunca apaga nada no Drive.
- Recuperação (ex.: computador formatado): ao conectar, o app procura a pasta que ele mesmo criou
  (o `drive.file` vale para os arquivos criados pelo mesmo projeto do Google Cloud) em vez de criar
  outra; arquivo ausente no PC é baixado do Drive. Se o PC já tem um arquivo diferente do Drive,
  a versão do Drive é copiada para "Histórico" (`…_substituido_AAAA-MM-DD_HHMMSS.json`) antes de
  ser sobrescrita. `restore` volta qualquer versão (atual ou do histórico) a pedido do usuário,
  guardando o arquivo local em `<nome>.pre-restauracao.bak`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from travas.settings import GoogleDriveSettings
from travas.tracking import secure_store
from travas.tracking.gcal import CalendarSync, GoogleCalendarError

log = logging.getLogger(__name__)

API = "https://www.googleapis.com/drive/v3"
UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"
FOLDER_MIME = "application/vnd.google-apps.folder"
HISTORY_FOLDER = "Histórico"


class GoogleDriveError(RuntimeError):
    pass


# ---- regra (pura) ------------------------------------------------------------------------------
@dataclass(frozen=True)
class Upload:
    key: str  # chave no estado: "atual/<nome>" ou "historico/<nome>"
    name: str  # nome do arquivo no Drive
    history: bool  # True = vai para a subpasta "Histórico"
    content: bytes
    sha256: str


def daily_name(name: str, day: dt.date) -> str:
    """acompanhamento.json → acompanhamento_2026-10-28.json"""
    path = Path(name)
    return f"{path.stem}_{day.isoformat()}{path.suffix}"


def plan_uploads(
    sources: dict[str, bytes], uploaded: dict[str, dict], day: dt.date, history: bool
) -> list[Upload]:
    """O que enviar: cada arquivo cujo conteúdo difere do último envio, como versão atual e
    (se `history`) como cópia do dia."""
    out = []
    for name, content in sources.items():
        sha = hashlib.sha256(content).hexdigest()
        targets = [(f"atual/{name}", name, False)]
        if history:
            dated = daily_name(name, day)
            targets.append((f"historico/{dated}", dated, True))
        for key, target, is_history in targets:
            if uploaded.get(key, {}).get("sha256") != sha:
                out.append(Upload(key, target, is_history, content, sha))
    return out


def restore_target(name: str, sources: list[str]) -> str | None:
    """Arquivo local que uma cópia do Drive restaura: o mesmo nome (versão atual) ou
    `<nome>_AAAA-MM-DD[...]` do histórico. None se não for de nenhum dos arquivos acompanhados."""
    for source in sources:
        path = Path(source)
        if name == source:
            return source
        pattern = rf"{re.escape(path.stem)}_\d{{4}}-\d{{2}}-\d{{2}}[\w-]*{re.escape(path.suffix)}"
        if re.fullmatch(pattern, name):
            return source
    return None


def validate_backup(content: bytes) -> dict:
    """Confere que a cópia é um arquivo da Carteira (`positions`) ou dos favoritos (`items`)."""
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoogleDriveError(f"cópia do Drive não é um JSON válido: {exc}") from exc
    if not isinstance(data, dict) or not any(
        isinstance(data.get(k), list) for k in ("positions", "items")
    ):
        raise GoogleDriveError("cópia do Drive não tem o formato da Carteira nem dos favoritos")
    return data


def multipart_body(metadata: dict, content: bytes, mime: str) -> tuple[bytes, str]:
    """Corpo `multipart/related` do upload do Drive (metadados + conteúdo) e o Content-Type."""
    boundary = secrets.token_hex(16)
    head = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata, ensure_ascii=False)}\r\n"
        f"--{boundary}\r\nContent-Type: {mime}\r\n\r\n"
    ).encode()
    tail = f"\r\n--{boundary}--\r\n".encode("ascii")
    return head + content + tail, f"multipart/related; boundary={boundary}"


def _q(text: str) -> str:
    """Texto entre aspas simples numa consulta do Drive."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


# ---- API do Drive ------------------------------------------------------------------------------
class DriveApi:
    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._token = token_provider

    def _send(self, method: str, url: str, data: bytes | None, content_type: str | None):
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"Bearer {self._token()}")
        if content_type:
            request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:  # noqa: S310
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise GoogleDriveError(f"API do Google Drive: {exc.code} {detail[:300]}") from exc
        return json.loads(raw.decode("utf-8")) if raw else None

    def alive(self, file_id: str) -> bool:
        """O arquivo/pasta existe e não está na lixeira."""
        url = f"{API}/files/{urllib.parse.quote(file_id)}?fields=id,trashed"
        try:
            info = self._send("GET", url, None, None)
        except GoogleDriveError as exc:
            if " 404 " in str(exc) or " 403 " in str(exc):
                return False
            raise
        return not info.get("trashed", False)

    def find_folder(self, name: str, parent: str | None = None) -> str | None:
        """Pasta criada pelo app com esse nome (a mais recente), fora da lixeira."""
        q = f"name = '{_q(name)}' and mimeType = '{FOLDER_MIME}' and trashed = false"
        if parent:
            q += f" and '{_q(parent)}' in parents"
        params = {"q": q, "orderBy": "modifiedTime desc", "fields": "files(id)", "pageSize": 10}
        found = self._send("GET", f"{API}/files?{urllib.parse.urlencode(params)}", None, None)
        files = found.get("files", [])
        return files[0]["id"] if files else None

    def children(self, folder: str) -> list[dict]:
        """Arquivos da pasta (id, nome, md5, data de modificação, tamanho)."""
        out, token = [], None
        while True:
            params = {
                "q": f"'{_q(folder)}' in parents and trashed = false",
                "fields": "nextPageToken, files(id,name,mimeType,md5Checksum,modifiedTime,size)",
                "pageSize": 1000,
            }
            if token:
                params["pageToken"] = token
            page = self._send("GET", f"{API}/files?{urllib.parse.urlencode(params)}", None, None)
            out.extend(f for f in page.get("files", []) if f.get("mimeType") != FOLDER_MIME)
            token = page.get("nextPageToken")
            if not token:
                return out

    def metadata(self, file_id: str) -> dict:
        url = f"{API}/files/{urllib.parse.quote(file_id)}?fields=id,name,parents,trashed"
        return self._send("GET", url, None, None)

    def download(self, file_id: str) -> bytes:
        url = f"{API}/files/{urllib.parse.quote(file_id)}?alt=media"
        request = urllib.request.Request(url, method="GET")
        request.add_header("Authorization", f"Bearer {self._token()}")
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:  # noqa: S310
                return resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise GoogleDriveError(f"API do Google Drive: {exc.code} {detail[:300]}") from exc

    def copy(self, file_id: str, name: str, parent: str) -> str:
        body = json.dumps({"name": name, "parents": [parent]}, ensure_ascii=False).encode("utf-8")
        url = f"{API}/files/{urllib.parse.quote(file_id)}/copy?fields=id"
        return self._send("POST", url, body, "application/json; charset=utf-8")["id"]

    def create_folder(self, name: str, parent: str | None = None) -> str:
        meta = {"name": name, "mimeType": FOLDER_MIME}
        if parent:
            meta["parents"] = [parent]
        body = json.dumps(meta, ensure_ascii=False).encode("utf-8")
        made = self._send("POST", f"{API}/files?fields=id", body, "application/json; charset=utf-8")
        return made["id"]

    def upload(self, name: str, content: bytes, parent: str, file_id: str | None) -> str:
        """Cria o arquivo (sem `file_id`) ou grava nova revisão do existente."""
        mime = "application/json"
        if file_id:
            body, ctype = multipart_body({"name": name}, content, mime)
            url = f"{UPLOAD_API}/files/{urllib.parse.quote(file_id)}?uploadType=multipart&fields=id"
            return self._send("PATCH", url, body, ctype)["id"]
        body, ctype = multipart_body({"name": name, "parents": [parent]}, content, mime)
        return self._send(
            "POST", f"{UPLOAD_API}/files?uploadType=multipart&fields=id", body, ctype
        )["id"]


# ---- serviço -----------------------------------------------------------------------------------
class DriveBackup:
    """Envio em segundo plano: pedido a cada mudança na Carteira e a cada `sync_minutes`."""

    def __init__(
        self,
        cfg: GoogleDriveSettings,
        state_file: Path,
        sources: list[Path],
        google: CalendarSync,
        on_restored: Callable[[], None] | None = None,
    ) -> None:
        self._cfg = cfg
        self._state_file = state_file
        self._sources = sources
        self._google = google
        self.on_restored = on_restored  # ex.: ressincronizar a agenda com a Carteira restaurada
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._folders_checked = False
        self.last_sync: str | None = None
        self.last_error: str | None = None
        self.last_result: dict | None = None
        self._thread: threading.Thread | None = None

    def _read_state(self) -> dict:
        if not self._state_file.exists():
            return {}
        return json.loads(self._state_file.read_text(encoding="utf-8"))

    def _write_state(self, state: dict) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._state_file)

    def status(self) -> dict:
        state = self._read_state()
        folder = state.get("folder_id")
        return {
            "enabled": self._cfg.enabled,
            "connected": self._google.connected(),
            "authorized": self._google.drive_ready(),
            "folder_name": self._cfg.folder_name,
            "folder_url": f"https://drive.google.com/drive/folders/{folder}" if folder else None,
            "files": [p.name for p in self._sources],
            "history": self._cfg.daily_history,
            "last_sync": self.last_sync,
            "last_error": self.last_error,
            "last_result": self.last_result,
        }

    def _folders(self, api: DriveApi, state: dict) -> dict:
        """Garante a pasta principal e a de histórico (recria se apagadas/na lixeira)."""
        if self._folders_checked and state.get("folder_id") and state.get("history_folder_id"):
            return state
        folder = state.get("folder_id")
        if not folder or not api.alive(folder):
            # Instalação nova (ou estado perdido): reaproveita a pasta que o app já criou.
            folder = api.find_folder(self._cfg.folder_name)
            if folder:
                log.info("Google Drive: pasta '%s' encontrada", self._cfg.folder_name)
            else:
                folder = api.create_folder(self._cfg.folder_name)
                log.info("Google Drive: pasta '%s' criada", self._cfg.folder_name)
            state = {"folder_id": folder, "files": self._adopt(api, folder, "atual")}
        history = state.get("history_folder_id")
        if not history or not api.alive(history):
            history = api.find_folder(HISTORY_FOLDER, folder) or api.create_folder(
                HISTORY_FOLDER, folder
            )
            files = {k: v for k, v in state.get("files", {}).items() if k.startswith("atual/")}
            state["files"] = {**files, **self._adopt(api, history, "historico")}
        state["history_folder_id"] = history
        self._write_state(state)
        self._folders_checked = True
        return state

    def _adopt(self, api: DriveApi, folder: str, kind: str) -> dict:
        """Arquivos já existentes na pasta, com o md5 do Drive (ainda sem sha256 de envio)."""
        names = [p.name for p in self._sources]
        return {
            f"{kind}/{f['name']}": {"id": f["id"], "md5": f.get("md5Checksum")}
            for f in api.children(folder)
            if restore_target(f["name"], names)
        }

    def _write_local(self, target: Path, content: bytes) -> Path | None:
        """Grava o arquivo local de forma atômica; o anterior vai para `.pre-restauracao.bak`."""
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = None
        if target.exists():
            backup = target.with_suffix(".pre-restauracao.bak")
            backup.write_bytes(target.read_bytes())
        tmp = target.with_suffix(".restauracao.tmp")
        tmp.write_bytes(content)
        os.replace(tmp, target)
        return backup

    def _restore_missing(self, api: DriveApi, files: dict) -> list[str]:
        """Arquivo acompanhado que não existe no PC (ex.: computador formatado): baixa a versão
        atual do Drive."""
        restored = []
        for path in self._sources:
            remote = files.get(f"atual/{path.name}")
            if path.exists() or not remote:
                continue
            content = api.download(remote["id"])
            validate_backup(content)
            self._write_local(path, content)
            remote["sha256"] = hashlib.sha256(content).hexdigest()
            restored.append(path.name)
            log.info("Google Drive: %s restaurado do Drive (ausente no computador)", path.name)
        return restored

    def sync(self) -> dict:
        with self._lock:
            if not self._cfg.enabled or not self._google.drive_ready():
                return {"skipped": True}
            api = DriveApi(self._google.access_token)
            state = self._folders(api, self._read_state())
            files = state.setdefault("files", {})
            restored = self._restore_missing(api, files)
            if restored:
                self._write_state(state)
            sources = {p.name: p.read_bytes() for p in self._sources if p.exists()}
            today = dt.datetime.now().astimezone().date()
            plan = plan_uploads(sources, files, today, self._cfg.daily_history)
            sent = []
            for item in plan:
                parent = state["history_folder_id" if item.history else "folder_id"]
                known = files.get(item.key, {})
                file_id = known.get("id")
                if file_id and "sha256" not in known:  # encontrado no Drive, nunca enviado daqui
                    if known.get("md5") == hashlib.md5(item.content).hexdigest():  # noqa: S324
                        files[item.key] = {**known, "sha256": item.sha256}
                        self._write_state(state)
                        continue
                    # Conteúdo diferente: preserva a versão do Drive antes de sobrescrever.
                    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    path = Path(item.name)
                    keep = f"{path.stem}_substituido_{stamp}{path.suffix}"
                    api.copy(file_id, keep, state["history_folder_id"])
                    log.info(
                        "Google Drive: versão anterior de %s guardada como %s", item.name, keep
                    )
                try:
                    new_id = api.upload(item.name, item.content, parent, file_id)
                except GoogleDriveError as exc:
                    if not file_id or " 404 " not in str(exc):
                        raise
                    new_id = api.upload(item.name, item.content, parent, None)  # apagado no Drive
                now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
                files[item.key] = {"id": new_id, "sha256": item.sha256, "uploaded_at": now}
                self._write_state(state)  # a cada arquivo: um erro no meio não reenvia o resto
                sent.append(item.name)
            result = {"uploaded": sent, "restored": restored, "files": len(sources)}
            self.last_sync = dt.datetime.now().astimezone().isoformat(timespec="seconds")
            self.last_error = None
            self.last_result = result
            if sent:
                log.info("Google Drive: enviados %s", sent)
        if restored and self.on_restored is not None:
            self.on_restored()
        return result

    def versions(self) -> list[dict]:
        """Cópias no Drive que podem ser restauradas: versões atuais primeiro, depois o
        histórico (mais recente primeiro)."""
        with self._lock:
            api = self._api()
            state = self._folders(api, self._read_state())
            names = [p.name for p in self._sources]
            out = []
            for kind in ("atual", "historico"):
                folder = state["folder_id" if kind == "atual" else "history_folder_id"]
                for f in api.children(folder):
                    target = restore_target(f["name"], names)
                    if target:
                        size = f.get("size")
                        out.append(
                            {
                                "id": f["id"],
                                "name": f["name"],
                                "kind": kind,
                                "target": target,
                                "modified": f.get("modifiedTime"),
                                "size": int(size) if size else None,
                            }
                        )
            out.sort(key=lambda v: (v["kind"] == "atual", v["modified"] or ""), reverse=True)
            return out

    def restore(self, file_id: str) -> dict:
        """Substitui o arquivo local pela cópia escolhida do Drive (o local vai para
        `.pre-restauracao.bak`)."""
        with self._lock:
            api = self._api()
            state = self._folders(api, self._read_state())
            meta = api.metadata(file_id)
            ours = {state["folder_id"], state["history_folder_id"]}
            if meta.get("trashed") or not ours & set(meta.get("parents", [])):
                raise GoogleDriveError("cópia fora da pasta do app no Drive")
            names = [p.name for p in self._sources]
            target = restore_target(meta["name"], names)
            path = next((p for p in self._sources if p.name == target), None)
            if path is None:
                raise GoogleDriveError(f"{meta['name']} não é um arquivo da Carteira")
            content = api.download(file_id)
            validate_backup(content)
            backup = self._write_local(path, content)
            log.info("Google Drive: %s restaurado de %s", path.name, meta["name"])
        if self.on_restored is not None:
            self.on_restored()  # agenda, alertas e o próprio Drive (envia a nova versão atual)
        return {
            "restored": meta["name"],
            "target": path.name,
            "backup": backup.name if backup else None,
        }

    def _api(self) -> DriveApi:
        if not self._cfg.enabled or not self._google.drive_ready():
            raise GoogleDriveError("Google Drive não autorizado: reconecte o Google")
        return DriveApi(self._google.access_token)

    def request_sync(self) -> None:
        self._wake.set()

    def start(self) -> None:
        if self._thread is not None or not self._cfg.enabled:
            return
        self._thread = threading.Thread(target=self._loop, name="gdrive-sync", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while True:
            try:
                self.sync()
            except (
                GoogleDriveError,
                GoogleCalendarError,
                OSError,
                secure_store.SecureStoreError,
                KeyError,
            ) as exc:
                self.last_error = str(exc)
                self._folders_checked = False
                log.warning("Google Drive: envio falhou: %s", exc)
            if self._wake.wait(self._cfg.sync_minutes * 60):
                # Junta gravações seguidas (ex.: editar várias estruturas) num envio só.
                time.sleep(self._cfg.debounce_seconds)
            self._wake.clear()
