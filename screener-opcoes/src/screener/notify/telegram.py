"""Cliente mínimo da Bot API do Telegram (sendMessage / sendPhoto) sobre urllib.

A lógica de aviso é escrita contra o protocolo `TelegramApi`, testável offline com um dublê.
O token nunca aparece em log nem em mensagem de erro.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.telegram.org"
PARSE_MODE = "HTML"


class NotifyError(RuntimeError):
    """Falha ao ler o token ou ao falar com a API do Telegram."""


class TelegramApi(Protocol):
    """Operações usadas para avisar um chat."""

    def send_message(self, text: str) -> None:
        """Envia texto formatado em HTML do Telegram."""

    def send_photo(self, photo: bytes, caption: str) -> None:
        """Envia uma imagem PNG com legenda em HTML do Telegram."""


def read_token(path: Path) -> str:
    """Token do bot guardado fora do repositório (arquivo de uma linha)."""
    file = path.expanduser()
    if not file.is_file():
        raise NotifyError(f"arquivo do token do Telegram não encontrado: {file}")
    token = file.read_text(encoding="utf-8").strip()
    if not token:
        raise NotifyError(f"arquivo do token do Telegram está vazio: {file}")
    return token


class HttpTelegram:
    """`TelegramApi` sobre HTTPS."""

    def __init__(self, token: str, chat_id: str, timeout: float) -> None:
        self._token = token
        self._chat_id = chat_id
        self._timeout = timeout

    def send_message(self, text: str) -> None:
        body = urlencode(
            {
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": PARSE_MODE,
                "disable_web_page_preview": "true",
            }
        ).encode()
        self._call("sendMessage", body, "application/x-www-form-urlencoded")

    def send_photo(self, photo: bytes, caption: str) -> None:
        fields = {"chat_id": self._chat_id, "caption": caption, "parse_mode": PARSE_MODE}
        body, content_type = _multipart(fields, "photo", "payoff.png", photo)
        self._call("sendPhoto", body, content_type)

    def _call(self, method: str, body: bytes, content_type: str) -> dict[str, Any]:
        request = Request(
            f"{API_BASE}/bot{self._token}/{method}",
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read())
        except HTTPError as exc:
            raise NotifyError(f"{method}: HTTP {exc.code} — {_description(exc)}") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise NotifyError(f"{method}: falha de rede ({exc})") from None
        if not payload.get("ok"):
            raise NotifyError(f"{method}: {payload.get('description', 'resposta sem ok')}")
        return payload


def _description(exc: HTTPError) -> str:
    """Motivo informado pela API (ex.: 'chat not found'), sem expor a URL com o token."""
    try:
        return str(json.loads(exc.read()).get("description", exc.reason))
    except ValueError, OSError:
        return str(exc.reason)


def _multipart(
    fields: dict[str, str], file_field: str, filename: str, content: bytes
) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
        f'filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode()
        + content
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"
