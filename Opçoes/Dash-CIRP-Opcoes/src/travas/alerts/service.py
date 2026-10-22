"""Alertas de stop 1:1 no app local.

Sem busca ativa: a cada avaliação da Carteira (cotações recebidas após uma ação do usuário)
o app (1) monta a lista vigiada das estruturas com o checkbox marcado e a envia ao servidor de
alertas, com as credenciais de envio; (2) com o mercado aberto, verifica se o ativo alcançou o
stop do dia e envia Telegram + e-mail. O alerta é reservado no servidor antes do envio, para que
app e servidor não mandem o mesmo alerta duas vezes; servidor fora do ar → o app envia mesmo assim.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import threading
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from travas.alerts.channels import deliver, delivered, read_contacts
from travas.alerts.server import fingerprint
from travas.alerts.stop_watch import JsonFile, SentLog, message, triggered, watch_entry
from travas.settings import AlertSettings

log = logging.getLogger(__name__)

ORIGIN = "app local (Dash CIRP, ao atualizar a Carteira)"


class ServerUnavailable(RuntimeError):
    pass


def armed_positions(records: list[dict]) -> dict[str, str]:
    """id → instante em que o alerta foi armado, das estruturas abertas com o checkbox marcado."""
    return {
        r["id"]: (r.get("stop_alert") or {}).get("armed_at") or ""
        for r in records
        if r.get("status") == "aberta" and (r.get("stop_alert") or {}).get("enabled")
    }


class StopAlerts:
    def __init__(
        self,
        cfg: AlertSettings,
        contacts_file: Path,
        sent_file: Path,
        records: Callable[[], list[dict]],
        google=None,  # CalendarSync (e-mail pela conexão Google), opcional
    ) -> None:
        self._cfg = cfg
        self._contacts_file = contacts_file
        self._sent = SentLog(sent_file)
        self._records = records
        self._google = google
        self._lock = threading.Lock()
        # id da estrutura → item vigiado; persistido para não esvaziar a lista do servidor
        # quando o app reinicia e só uma estrutura é reavaliada.
        self._watch_file = JsonFile(sent_file.with_name("alertas_vigiados.json"), {"entries": {}})
        self._entries: dict[str, dict] = self._watch_file.read()["entries"]
        self._pushed: str | None = None
        self.server_status: dict | None = None
        self.server_error: str | None = None
        self.last_error: str | None = None
        self.last_sent: dict | None = None

    # ---- servidor ----
    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        if not self._cfg.server_url:
            raise ServerUnavailable("servidor de alertas não configurado")
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            self._cfg.server_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._cfg.timeout_seconds) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8") or "{}")
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise ServerUnavailable(f"servidor de alertas inacessível: {exc}") from exc

    def _credentials(self) -> dict:
        contacts = read_contacts(self._contacts_file)
        google = None
        if self._google is not None:
            try:
                google = self._google.server_credentials()
            except Exception as exc:  # noqa: BLE001 — sem e-mail no servidor, Telegram segue
                log.warning("alertas: credencial do Google indisponível: %s", exc)
        return {
            "telegram": {"bot_token": contacts.bot_token, "chat_id": contacts.chat_id},
            "email": contacts.email,
            "google": google,
        }

    def _sync_server(self) -> None:
        if not self._cfg.server_url:
            return
        try:
            entries = sorted(self._entries.values(), key=lambda e: e["key"])
            digest = hashlib.sha256(
                json.dumps(entries, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            if digest != self._pushed:
                self._request("PUT", "/watch", {"entries": entries})
                self._pushed = digest
            status = self._request("GET", "/status")
            creds = self._credentials()
            if fingerprint(creds) != status.get("credentials_fingerprint"):
                self._request("PUT", "/credentials", creds)
                status = self._request("GET", "/status")
            sent = self._request("GET", "/sent").get("sent", {})
            keys = {e["key"] for e in entries}
            self._sent.merge({k: v for k, v in sent.items() if k in keys})
            self.server_status, self.server_error = status, None
        except ServerUnavailable as exc:
            self.server_error = str(exc)
            log.warning("alertas: %s", exc)

    # ---- fluxo ----
    def request_sync(self) -> None:
        """Estrutura alterada/encerrada/desmarcada: atualiza a lista do servidor (sem cotações)."""
        if not self._cfg.enabled:
            return
        threading.Thread(target=self._resync, name="alertas-sync", daemon=True).start()

    def _resync(self) -> None:
        with self._lock:
            self._refresh_entries([])
            self._sync_server()

    def _refresh_entries(self, evaluated: list[dict]) -> dict[str, str]:
        armed = armed_positions(self._records())
        for e in evaluated:
            if e["id"] in armed:
                entry = watch_entry(e, armed[e["id"]])
                if entry is not None:
                    self._entries[e["id"]] = entry
                else:
                    self._entries.pop(e["id"], None)
        for pid in list(self._entries):
            if pid not in armed:
                del self._entries[pid]
            else:  # rearmado sem nova avaliação: mesma tabela, chave nova
                self._entries[pid]["key"] = f"{pid}:{armed[pid]}"
        self._watch_file.write({"entries": self._entries})
        return armed

    def process(self, evaluated: list[dict], market_open: bool, wait: bool = False) -> None:
        if not self._cfg.enabled:
            return
        thread = threading.Thread(
            target=self._process, args=(evaluated, market_open), name="alertas", daemon=True
        )
        thread.start()
        if wait:
            thread.join()

    def _process(self, evaluated: list[dict], market_open: bool) -> None:
        with self._lock:
            try:
                self._refresh_entries(evaluated)
                self._sync_server()
                if not market_open:
                    return
                today = dt.date.today()
                for e in evaluated:
                    entry = self._entries.get(e["id"])
                    if entry is None:
                        continue
                    price = triggered(entry, e.get("spot"), today)
                    if price is not None:
                        self._alert(entry, e["spot"], price, e.get("pnl_natural"))
            except Exception as exc:  # noqa: BLE001 — alerta nunca derruba a avaliação
                self.last_error = str(exc)
                log.exception("alertas: falha")

    def _gmail_token(self):
        if self._google is None or not self._google.gmail_ready():
            return None
        return self._google.access_token

    def _alert(self, entry: dict, spot: float, price: float, pnl_now: float | None) -> None:
        key = entry["key"]
        if self._sent.has(key):
            return
        now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        claim = {"by": "app local", "at": now, "spot": spot, "stop_price": price}
        server_ok = True
        try:
            reserve = {"key": key, "info": {**claim, "status": "enviando"}}
            if not self._request("POST", "/sent", reserve)["added"]:
                self._sent.add(key, {"by": "servidor", "at": now, "status": "enviado"})
                return  # o servidor já enviou (ou está enviando)
        except (ServerUnavailable, KeyError) as exc:
            server_ok = False
            self.server_error = str(exc)
        subject, text = message(entry, spot, price, ORIGIN, pnl_now)
        status = deliver(read_contacts(self._contacts_file), subject, text, self._gmail_token())
        if delivered(status):
            info = {**claim, "status": "enviado", "channels": status}
            self._sent.add(key, info)
            self.last_sent = {"key": key, "name": entry["name"], **info}
            log.info("alerta de stop enviado: %s %s", entry["name"], status)
            if server_ok:
                self._safe("/sent/update", {"key": key, "info": info})
        else:
            self.last_error = f"envio do alerta de {entry['name']} falhou: {status}"
            if server_ok:
                self._safe("/sent/release", {"key": key})

    def _safe(self, path: str, body: dict) -> None:
        try:
            self._request("POST", path, body)
        except ServerUnavailable as exc:
            self.server_error = str(exc)

    # ---- interface ----
    def sent_info(self, position_id: str, armed_at: str) -> dict | None:
        return self._sent.all().get(f"{position_id}:{armed_at}")

    def status(self) -> dict:
        contacts = read_contacts(self._contacts_file)
        email = contacts.email
        masked = f"{email[:2]}…@{email.split('@')[1]}" if email else None
        return {
            "enabled": self._cfg.enabled,
            "contacts_file": self._contacts_file.name,
            "telegram": contacts.telegram_ready,
            "email": masked,
            "gmail": bool(self._google is not None and self._google.gmail_ready()),
            "google_connected": bool(self._google is not None and self._google.connected()),
            "server_url": self._cfg.server_url,
            "server": self.server_status,
            "server_error": self.server_error,
            "armed": len(armed_positions(self._records())),
            "last_error": self.last_error,
            "last_sent": self.last_sent,
        }

    def test(self) -> dict:
        """Mensagem de teste pelos canais do app e pelos do servidor."""
        now = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
        text = (
            f"✅ Teste dos alertas de stop 1:1 do Dash CIRP ({now}), enviado pelo app local. "
            "Nenhuma ordem é enviada."
        )
        local = deliver(
            read_contacts(self._contacts_file),
            "Teste dos alertas do Dash CIRP",
            text,
            self._gmail_token(),
        )
        with self._lock:
            self._sync_server()
        try:
            server = self._request("POST", "/test", {"key": "teste"})
        except ServerUnavailable as exc:
            server = {"error": str(exc)}
        return {"local": local, "server": server}
