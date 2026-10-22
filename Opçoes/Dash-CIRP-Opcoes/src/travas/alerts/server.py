"""Servidor HTTP dos alertas no Debian (só biblioteca padrão; escuta só na interface do
Tailscale). O app local envia a lista vigiada e as credenciais de envio; a checagem do servidor
(`travas alerts-check`, a cada 15 min de pregão) e o app consultam/registram os alertas enviados,
para que o mesmo alerta não saia duas vezes.

    python3 -m travas.alerts.server --dir ~/alerts --host 100.113.24.44 --port 8767

Arquivos em --dir: watch.json, credentials.json (chmod 600), sent.json, check.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.server
import json
from pathlib import Path

from travas.alerts.channels import Contacts, deliver, google_access_token
from travas.alerts.stop_watch import JsonFile, SentLog

MAX_BODY = 2_000_000


def fingerprint(credentials: dict) -> str:
    text = json.dumps(credentials, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def contacts_from(creds: dict) -> tuple[Contacts, object]:
    """Contatos e função de access token do Gmail (None sem autorização) das credenciais."""
    tg = creds.get("telegram") or {}
    contacts = Contacts(tg.get("bot_token"), tg.get("chat_id"), creds.get("email"))
    google = creds.get("google") or {}
    if not google.get("refresh_token"):
        return contacts, None

    def token() -> str:
        return google_access_token(
            google["client_id"], google["client_secret"], google["refresh_token"]
        )

    return contacts, token


class AlertStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.watch = JsonFile(root / "watch.json", {"entries": [], "updated_at": None})
        self.credentials = JsonFile(root / "credentials.json", {})
        self.check = JsonFile(root / "check.json", {})
        self.sent = SentLog(root / "sent.json")

    def status(self) -> dict:
        watch = self.watch.read()
        creds = self.credentials.read()
        google = creds.get("google") or {}
        return {
            "watch": len(watch["entries"]),
            "watch_updated_at": watch.get("updated_at"),
            "credentials_fingerprint": fingerprint(creds) if creds else None,
            "telegram": bool((creds.get("telegram") or {}).get("bot_token")),
            "email": bool(creds.get("email") and google.get("refresh_token")),
            "sent": len(self.sent.all()),
            "last_check": self.check.read() or None,
        }


def make_handler(store: AlertStore):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "travas-alerts"

        def _send(self, code: int, body: dict) -> None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> dict | None:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                self._send(413 if length else 400, {"error": "corpo ausente ou grande demais"})
                return None
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except ValueError:  # UnicodeDecodeError ou JSONDecodeError
                self._send(400, {"error": "JSON inválido"})
                return None
            if not isinstance(body, dict):
                self._send(400, {"error": "esperado um objeto JSON"})
                return None
            return body

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/status":
                self._send(200, store.status())
            elif self.path == "/watch":
                self._send(200, store.watch.read())
            elif self.path == "/sent":
                self._send(200, {"sent": store.sent.all()})
            else:
                self._send(404, {"error": "rota desconhecida"})

        def do_PUT(self) -> None:  # noqa: N802
            body = self._body()
            if body is None:
                return
            if self.path == "/watch":
                entries = body.get("entries")
                if not isinstance(entries, list):
                    self._send(400, {"error": "entries deve ser uma lista"})
                    return
                now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
                with store.watch.lock:
                    store.watch.write({"entries": entries, "updated_at": now})
                self._send(200, {"ok": True, "watch": len(entries)})
            elif self.path == "/credentials":
                with store.credentials.lock:
                    store.credentials.write(body, private=True)
                self._send(200, {"ok": True, "credentials_fingerprint": fingerprint(body)})
            else:
                self._send(404, {"error": "rota desconhecida"})

        def do_POST(self) -> None:  # noqa: N802
            body = self._body()
            if body is None:
                return
            key = body.get("key")
            if not isinstance(key, str):
                self._send(400, {"error": "key ausente"})
            elif self.path == "/sent":  # reserva antes de enviar: False = já enviado/reservado
                self._send(200, {"added": store.sent.add(key, body.get("info") or {})})
            elif self.path == "/sent/update":
                store.sent.update(key, body.get("info") or {})
                self._send(200, {"ok": True})
            elif self.path == "/sent/release":
                store.sent.remove(key)
                self._send(200, {"ok": True})
            elif self.path == "/test":
                contacts, gmail = contacts_from(store.credentials.read())
                now = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
                text = (
                    f"✅ Teste dos alertas de stop 1:1 do Dash CIRP ({now}), enviado pelo "
                    "servidor Debian. Nenhuma ordem é enviada."
                )
                self._send(200, deliver(contacts, "Teste dos alertas (servidor)", text, gmail))
            else:
                self._send(404, {"error": "rota desconhecida"})

        def log_message(self, fmt: str, *args) -> None:
            return  # sem log de acesso

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="servidor HTTP dos alertas de stop")
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    args.dir.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(
        (args.host, args.port), make_handler(AlertStore(args.dir))
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
