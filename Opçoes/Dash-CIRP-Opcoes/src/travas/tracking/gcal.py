"""Google Agenda: um evento por vencimento de cada estrutura ABERTA da Carteira, com
lembretes antes do vencimento; evento apagado quando a estrutura é encerrada ou excluída.

- Permissão mínima: escopo `calendar.app.created` — o app só enxerga e altera agendas criadas por
  ele (cria a agenda "Dash CIRP – Vencimentos"); a agenda pessoal fica fora do alcance.
- OAuth de app para computador (loopback 127.0.0.1 + PKCE). O login e o consentimento são feitos
  pelo usuário no navegador; o app nunca vê a senha. O refresh token fica cifrado pela DPAPI do
  Windows (`secure_store`) em `data/google_agenda.json`, junto com o id da agenda.
- Sincronização por reconciliação: cada evento leva em `extendedProperties.private` o id da
  estrutura e o vencimento; a agenda é a fonte da verdade (sem estado local a corromper).
  `plan_sync` (função pura) decide o que criar, atualizar e apagar.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import http.server
import json
import logging
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from travas.calendar_b3 import B3Calendar
from travas.settings import GoogleCalendarSettings
from travas.timeutils import LOCAL_TIMEZONE
from travas.tracking import secure_store

log = logging.getLogger(__name__)

CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.app.created"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"  # alertas de stop por e-mail
SCOPE = f"{CALENDAR_SCOPE} {GMAIL_SCOPE}"
API = "https://www.googleapis.com/calendar/v3"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
MARKER = "dashcirp"
MAX_REMINDERS = 5  # limite do Google por evento
MAX_REMINDER_MINUTES = 40320  # 4 semanas
CONNECT_TIMEOUT_SECONDS = 300


class GoogleCalendarError(RuntimeError):
    pass


# ---- regra (pura) ------------------------------------------------------------------------------
def _hhmm(text: str) -> dt.time:
    hours, minutes = text.split(":")
    return dt.time(int(hours), int(minutes))


def reminder_minutes(
    expiration: dt.date, calendar: B3Calendar, cfg: GoogleCalendarSettings
) -> list[int]:
    """Minutos antes do início do evento para cada lembrete (pregões antes do vencimento)."""
    start = dt.datetime.combine(expiration, _hhmm(cfg.event_time))
    out = []
    for r in cfg.reminders:
        day = (
            expiration
            if r.business_days_before == 0
            else calendar.previous_sessions(expiration, r.business_days_before)[0]
        )
        minutes = int((start - dt.datetime.combine(day, _hhmm(r.time))).total_seconds() // 60)
        if 0 <= minutes <= MAX_REMINDER_MINUTES:
            out.append(minutes)
    return sorted(set(out))[:MAX_REMINDERS]


def _legs_text(record: dict) -> list[str]:
    lines = []
    for leg in record.get("legs", []):
        side = "Compra" if leg.get("side") == "compra" else "Venda"
        kind = leg.get("option_type") or ""
        strike = leg.get("strike")
        strike_txt = f" {strike:.2f}".replace(".", ",") if isinstance(strike, int | float) else ""
        lines.append(f"• {side} {leg.get('quantity')} {leg.get('symbol', '')} {kind}{strike_txt}")
    return lines


def desired_events(
    positions: list[dict], calendar: B3Calendar, cfg: GoogleCalendarSettings
) -> dict[str, dict]:
    """Eventos que devem existir: um por (estrutura aberta, vencimento das pernas)."""
    out: dict[str, dict] = {}
    for record in positions:
        if record.get("status") != "aberta":
            continue
        expirations = sorted(
            {
                dt.date.fromisoformat(str(leg["expiration"]))
                for leg in record.get("legs", [])
                if leg.get("expiration")
            }
        )
        for expiration in expirations:
            key = f"{record['id']}|{expiration.isoformat()}"
            start = dt.datetime.combine(expiration, _hhmm(cfg.event_time))
            end = start + dt.timedelta(minutes=cfg.event_minutes)
            underlying = record.get("underlying", "")
            name = record.get("name") or underlying
            multi = len(expirations) > 1
            description = "\n".join(
                [
                    f"Estrutura aberta no Dash CIRP: {name} ({record.get('underlying', '')})",
                    f"Grupo: {record.get('group') or 'Sem grupo'} · entrada em "
                    f"{record.get('entry_date', '—')}",
                    *(["Pernas com vencimentos diferentes: este é um deles."] if multi else []),
                    *_legs_text(record),
                    "",
                    "Decidir: encerrar, rolar ou deixar exercer, antes do fim da negociação da "
                    "série no dia do vencimento.",
                    "Evento gerenciado pelo Dash: é apagado quando a estrutura for encerrada.",
                ]
            )
            body = {
                "summary": f"Vencimento {expiration:%d/%m} · {name} ({underlying})",
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": LOCAL_TIMEZONE},
                "end": {"dateTime": end.isoformat(), "timeZone": LOCAL_TIMEZONE},
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": m}
                        for m in reminder_minutes(expiration, calendar, cfg)
                    ],
                },
            }
            fingerprint = hashlib.sha1(
                json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()[:16]
            body["extendedProperties"] = {
                "private": {
                    MARKER: "1",
                    "position": record["id"],
                    "expiration": expiration.isoformat(),
                    "fingerprint": fingerprint,
                }
            }
            out[key] = body
    return out


def event_key(event: dict) -> str | None:
    private = (event.get("extendedProperties") or {}).get("private") or {}
    if private.get(MARKER) != "1":
        return None
    return f"{private.get('position')}|{private.get('expiration')}"


@dataclass
class SyncPlan:
    create: list[dict] = field(default_factory=list)
    update: list[tuple[str, dict]] = field(default_factory=list)  # (event_id, body)
    delete: list[str] = field(default_factory=list)  # event_id


def plan_sync(desired: dict[str, dict], existing: list[dict]) -> SyncPlan:
    """Compara o desejado com os eventos do Dash na agenda (duplicados também são apagados)."""
    plan = SyncPlan()
    seen: set[str] = set()
    for event in existing:
        key = event_key(event)
        if key is None:
            continue
        if key not in desired or key in seen:
            plan.delete.append(event["id"])
            continue
        seen.add(key)
        want = desired[key]["extendedProperties"]["private"]["fingerprint"]
        have = event["extendedProperties"]["private"].get("fingerprint")
        if want != have:
            plan.update.append((event["id"], desired[key]))
    plan.create = [body for key, body in desired.items() if key not in seen]
    return plan


# ---- OAuth (app para computador, loopback + PKCE) ----------------------------------------------
def _post_form(url: str, data: dict, timeout: float = 20) -> dict:
    payload = urllib.parse.urlencode(data).encode("ascii")
    request = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise GoogleCalendarError(f"Google recusou ({exc.code}): {detail[:300]}") from exc


class OAuthClient:
    def __init__(self, client_secret_file: Path) -> None:
        data = json.loads(client_secret_file.read_text(encoding="utf-8"))
        if "installed" not in data:
            raise GoogleCalendarError(
                "a credencial OAuth precisa ser do tipo 'App para computador' (installed)"
            )
        info = data["installed"]
        self.client_id = info["client_id"]
        self._client_secret = info["client_secret"]
        self.auth_uri = info["auth_uri"]
        self.client_secret = self._client_secret
        self.token_uri = info["token_uri"]

    def authorization(self) -> tuple[str, Callable[[float], tuple[str, str]]]:
        """URL de consentimento e uma função que espera o retorno do Google no loopback e
        devolve (refresh token, escopos concedidos)."""
        verifier = secrets.token_urlsafe(64)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
            .decode("ascii")
            .rstrip("=")
        )
        state = secrets.token_urlsafe(16)
        result: dict[str, str] = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if query.get("state", [""])[0] != state:
                    self.send_response(400)
                    self.end_headers()
                    return
                result.update({k: v[0] for k, v in query.items()})
                ok = "code" in query
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                message = (
                    "Google conectado ao Dash CIRP. Pode fechar esta aba."
                    if ok
                    else "Autorização não concedida. Pode fechar esta aba."
                )
                self.wfile.write(f"<p style='font:16px sans-serif'>{message}</p>".encode())

            def log_message(self, *args) -> None:  # sem log de acesso (a URL tem o código)
                return

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        redirect = f"http://127.0.0.1:{server.server_address[1]}/"
        url = (
            self.auth_uri
            + "?"
            + urllib.parse.urlencode(
                {
                    "client_id": self.client_id,
                    "redirect_uri": redirect,
                    "response_type": "code",
                    "scope": SCOPE,
                    "access_type": "offline",
                    "prompt": "consent",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "state": state,
                }
            )
        )

        def wait(timeout: float) -> tuple[str, str]:
            deadline = time.monotonic() + timeout
            server.timeout = 1.0
            try:
                while not result and time.monotonic() < deadline:
                    server.handle_request()
            finally:
                server.server_close()
            if "code" not in result:
                reason = result.get("error", "tempo esgotado sem resposta do Google")
                raise GoogleCalendarError(f"autorização não concluída: {reason}")
            tokens = _post_form(
                self.token_uri,
                {
                    "code": result["code"],
                    "client_id": self.client_id,
                    "client_secret": self._client_secret,
                    "code_verifier": verifier,
                    "redirect_uri": redirect,
                    "grant_type": "authorization_code",
                },
            )
            if "refresh_token" not in tokens:
                raise GoogleCalendarError("o Google não devolveu refresh token")
            return tokens["refresh_token"], tokens.get("scope", CALENDAR_SCOPE)

        return url, wait

    def access_token(self, refresh_token: str) -> tuple[str, float]:
        tokens = _post_form(
            self.token_uri,
            {
                "client_id": self.client_id,
                "client_secret": self._client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        return tokens["access_token"], time.monotonic() + float(tokens.get("expires_in", 3600))

    @staticmethod
    def revoke(refresh_token: str) -> None:
        _post_form(REVOKE_URL, {"token": refresh_token})


# ---- API da agenda -----------------------------------------------------------------------------
class CalendarApi:
    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._token = token_provider

    def request(self, method: str, path: str, params: dict | None = None, body=None):
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"Bearer {self._token()}")
        if data is not None:
            request.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(request, timeout=30) as resp:  # noqa: S310
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise GoogleCalendarError(f"API do Google Agenda: {exc.code} {detail[:300]}") from exc
        return json.loads(raw.decode("utf-8")) if raw else None

    def create_calendar(self, name: str) -> str:
        made = self.request(
            "POST",
            "/calendars",
            body={
                "summary": name,
                "timeZone": LOCAL_TIMEZONE,
                "description": "Vencimentos das estruturas abertas no Dash CIRP Opções "
                "(gerenciada pelo app).",
            },
        )
        return made["id"]

    def calendar_exists(self, calendar_id: str) -> bool:
        try:
            self.request("GET", f"/calendars/{urllib.parse.quote(calendar_id)}")
        except GoogleCalendarError as exc:
            if " 404 " in str(exc) or " 403 " in str(exc):
                return False
            raise
        return True

    def dash_events(self, calendar_id: str) -> list[dict]:
        events, token = [], None
        while True:
            params = {
                "privateExtendedProperty": f"{MARKER}=1",
                "maxResults": 2500,
                "showDeleted": "false",
                "singleEvents": "true",
            }
            if token:
                params["pageToken"] = token
            path = f"/calendars/{urllib.parse.quote(calendar_id)}/events"
            page = self.request("GET", path, params)
            events.extend(page.get("items", []))
            token = page.get("nextPageToken")
            if not token:
                return events

    def apply(self, calendar_id: str, plan: SyncPlan) -> None:
        base = f"/calendars/{urllib.parse.quote(calendar_id)}/events"
        for body in plan.create:
            self.request("POST", base, body=body)
        for event_id, body in plan.update:
            self.request("PUT", f"{base}/{urllib.parse.quote(event_id)}", body=body)
        for event_id in plan.delete:
            try:
                self.request("DELETE", f"{base}/{urllib.parse.quote(event_id)}")
            except GoogleCalendarError as exc:
                if " 410 " not in str(exc) and " 404 " not in str(exc):  # já apagado
                    raise


# ---- serviço -----------------------------------------------------------------------------------
def find_client_secret(root: Path, pattern: str) -> Path | None:
    found = sorted(root.glob(pattern))
    return found[0] if found else None


class CalendarSync:
    """Conexão, estado e sincronização em segundo plano (pedido imediato a cada mudança no
    Carteira e a cada `sync_minutes`)."""

    def __init__(
        self,
        cfg: GoogleCalendarSettings,
        state_file: Path,
        project_root: Path,
        positions: Callable[[], list[dict]],
        calendar: B3Calendar,
    ) -> None:
        self._cfg = cfg
        self._state_file = state_file
        self._root = project_root
        self._positions = positions
        self._calendar = calendar
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._access: tuple[str, float] | None = None
        self.connecting = False
        self.last_sync: str | None = None
        self.last_error: str | None = None
        self.last_result: dict | None = None
        self._thread: threading.Thread | None = None

    # estado persistido (id da agenda + refresh token cifrado)
    def _read_state(self) -> dict:
        if not self._state_file.exists():
            return {}
        return json.loads(self._state_file.read_text(encoding="utf-8"))

    def _write_state(self, state: dict) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(self._state_file)

    def _oauth(self) -> OAuthClient:
        path = find_client_secret(self._root, self._cfg.client_secret_glob)
        if path is None:
            raise GoogleCalendarError(
                f"credencial OAuth não encontrada ({self._cfg.client_secret_glob} na pasta do "
                "projeto)"
            )
        return OAuthClient(path)

    def connected(self) -> bool:
        return "refresh_token" in self._read_state()

    def status(self) -> dict:
        state = self._read_state()
        return {
            "enabled": self._cfg.enabled,
            "configured": find_client_secret(self._root, self._cfg.client_secret_glob) is not None,
            "connected": "refresh_token" in state,
            "gmail": self.gmail_ready(),
            "connecting": self.connecting,
            "calendar_name": self._cfg.calendar_name,
            "calendar_ready": bool(state.get("calendar_id")),
            "last_sync": self.last_sync,
            "last_error": self.last_error,
            "last_result": self.last_result,
            "reminders": [r.model_dump() for r in self._cfg.reminders],
            "event_time": self._cfg.event_time,
        }

    def begin_connect(self) -> str:
        """Devolve a URL de consentimento; o retorno é esperado em segundo plano."""
        oauth = self._oauth()
        url, wait = oauth.authorization()
        self.connecting = True
        self.last_error = None

        def finish() -> None:
            try:
                refresh, scopes = wait(CONNECT_TIMEOUT_SECONDS)
                state = self._read_state()
                state["refresh_token"] = secure_store.protect(refresh)
                state["scopes"] = scopes
                self._write_state(state)
                self._access = None
                log.info("Google Agenda conectado")
                self.request_sync()
            except (GoogleCalendarError, OSError, secure_store.SecureStoreError) as exc:
                self.last_error = str(exc)
                log.warning("Google Agenda: conexão falhou: %s", exc)
            finally:
                self.connecting = False

        threading.Thread(target=finish, name="gcal-connect", daemon=True).start()
        return url

    def disconnect(self) -> None:
        state = self._read_state()
        token = state.pop("refresh_token", None)
        state.pop("scopes", None)
        if token:
            try:
                OAuthClient.revoke(secure_store.unprotect(token))
            except (GoogleCalendarError, OSError, secure_store.SecureStoreError) as exc:
                log.warning("Google Agenda: revogação falhou (token apagado mesmo assim): %s", exc)
        self._write_state(state)
        self._access = None
        self.last_result = None

    def gmail_ready(self) -> bool:
        state = self._read_state()
        return "refresh_token" in state and GMAIL_SCOPE in state.get("scopes", "").split()

    def access_token(self) -> str:
        """Access token da conexão (agenda e, se concedido, gmail.send)."""
        return self._token()

    def server_credentials(self) -> dict | None:
        """Cliente OAuth + refresh token, para o servidor de alertas enviar e-mail sozinho.
        None se o e-mail não foi autorizado."""
        if not self.gmail_ready():
            return None
        oauth = self._oauth()
        return {
            "client_id": oauth.client_id,
            "client_secret": oauth.client_secret,
            "refresh_token": secure_store.unprotect(self._read_state()["refresh_token"]),
        }

    def _token(self) -> str:
        if self._access and time.monotonic() < self._access[1] - 60:
            return self._access[0]
        state = self._read_state()
        if "refresh_token" not in state:
            raise GoogleCalendarError("Google Agenda não conectado")
        refresh = secure_store.unprotect(state["refresh_token"])
        try:
            self._access = self._oauth().access_token(refresh)
        except GoogleCalendarError as exc:
            if "invalid_grant" in str(exc):  # acesso revogado ou expirado: pedir nova conexão
                state.pop("refresh_token", None)
                self._write_state(state)
                raise GoogleCalendarError(
                    "autorização do Google expirada ou revogada: conecte de novo"
                ) from exc
            raise
        return self._access[0]

    def sync(self) -> dict:
        with self._lock:
            if not self._cfg.enabled or not self.connected():
                return {"skipped": True}
            api = CalendarApi(self._token)
            state = self._read_state()
            calendar_id = state.get("calendar_id")
            if not calendar_id or not api.calendar_exists(calendar_id):
                calendar_id = api.create_calendar(self._cfg.calendar_name)
                state = self._read_state()
                state["calendar_id"] = calendar_id
                self._write_state(state)
                log.info("Google Agenda: agenda '%s' criada", self._cfg.calendar_name)
            desired = desired_events(self._positions(), self._calendar, self._cfg)
            plan = plan_sync(desired, api.dash_events(calendar_id))
            api.apply(calendar_id, plan)
            result = {
                "created": len(plan.create),
                "updated": len(plan.update),
                "deleted": len(plan.delete),
                "events": len(desired),
            }
            self.last_sync = dt.datetime.now().astimezone().isoformat(timespec="seconds")
            self.last_error = None
            self.last_result = result
            if plan.create or plan.update or plan.delete:
                log.info("Google Agenda sincronizado: %s", result)
            return result

    def request_sync(self) -> None:
        self._wake.set()

    def start(self) -> None:
        if self._thread is not None or not self._cfg.enabled:
            return
        self._thread = threading.Thread(target=self._loop, name="gcal-sync", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while True:
            try:
                self.sync()
            except (GoogleCalendarError, OSError, secure_store.SecureStoreError, KeyError) as exc:
                self.last_error = str(exc)
                log.warning("Google Agenda: sincronização falhou: %s", exc)
            self._wake.wait(self._cfg.sync_minutes * 60)
            self._wake.clear()
