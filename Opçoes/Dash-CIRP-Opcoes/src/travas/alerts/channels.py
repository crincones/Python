"""Canais de envio: bot do Telegram e e-mail pela Gmail API (só biblioteca padrão).

Os dados de contato vêm do arquivo `telegram-token.txt` (fora do git): uma linha com o token do
bot (`123456:ABC…`), uma com o chat id (número) e uma com o e-mail. O formato de cada linha é
reconhecido pelo conteúdo, com ou sem rótulo ("token: …", "chat_id = …").
"""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path

TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"
TIMEOUT = 20

_TOKEN = re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CHAT = re.compile(r"(?<![\w:])-?\d{5,}(?![\w:])")


class AlertChannelError(RuntimeError):
    """Falha de envio; a mensagem não contém tokens."""


@dataclass(frozen=True)
class Contacts:
    bot_token: str | None
    chat_id: str | None
    email: str | None

    @property
    def telegram_ready(self) -> bool:
        return bool(self.bot_token and self.chat_id)


def parse_contacts(text: str) -> Contacts:
    token = chat = email = None
    for line in text.splitlines():
        if token is None and (m := _TOKEN.search(line)):
            token = m.group(0)
            continue
        if email is None and (m := _EMAIL.search(line)):
            email = m.group(0)
            continue
        if chat is None and (m := _CHAT.search(line)):
            chat = m.group(0)
    return Contacts(token, chat, email)


def read_contacts(path: Path) -> Contacts:
    if not path.exists():
        return Contacts(None, None, None)
    return parse_contacts(path.read_text(encoding="utf-8-sig"))


def _post(request: urllib.request.Request, what: str) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise AlertChannelError(f"{what} recusou ({exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AlertChannelError(f"{what} inacessível: {exc}") from exc


def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode("utf-8")
    request = urllib.request.Request(TELEGRAM_URL.format(token=bot_token), data=data)
    try:
        body = _post(request, "Telegram")
    except AlertChannelError as exc:  # a URL tem o token: não deixar vazar na mensagem
        raise AlertChannelError(str(exc).replace(bot_token, "<token>")) from None
    if not body.get("ok"):
        raise AlertChannelError(f"Telegram recusou: {body.get('description', body)}")


def google_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("ascii")
    body = _post(urllib.request.Request(GOOGLE_TOKEN_URL, data=data), "Google (token)")
    if "access_token" not in body:
        raise AlertChannelError("Google não devolveu access token")
    return body["access_token"]


def build_email(to: str, subject: str, text: str) -> bytes:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(text)
    return msg.as_bytes()


def send_gmail(access_token: str, to: str, subject: str, text: str) -> None:
    raw = base64.urlsafe_b64encode(build_email(to, subject, text)).decode("ascii")
    request = urllib.request.Request(
        GMAIL_SEND_URL,
        data=json.dumps({"raw": raw}).encode("utf-8"),
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    )
    _post(request, "Gmail")


def deliver(contacts: Contacts, subject: str, text: str, gmail_token) -> dict[str, str]:
    """Envia pelos canais configurados; devolve o estado de cada um ("ok" ou o erro).
    `gmail_token`: função que devolve um access token com gmail.send (ou None: sem e-mail)."""
    status: dict[str, str] = {}
    if contacts.telegram_ready:
        try:
            send_telegram(contacts.bot_token, contacts.chat_id, text)
            status["telegram"] = "ok"
        except AlertChannelError as exc:
            status["telegram"] = str(exc)
    else:
        status["telegram"] = "não configurado"
    if contacts.email and gmail_token is not None:
        try:
            send_gmail(gmail_token(), contacts.email, subject, text)
            status["email"] = "ok"
        except (AlertChannelError, RuntimeError, OSError) as exc:
            status["email"] = str(exc)
    else:
        status["email"] = "não configurado" if not contacts.email else "Gmail não autorizado"
    return status


def delivered(status: dict[str, str]) -> bool:
    return any(v == "ok" for v in status.values())
