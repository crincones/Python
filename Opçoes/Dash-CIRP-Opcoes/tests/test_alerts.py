"""Alertas de stop 1:1: contatos, lista vigiada, gatilho, servidor HTTP e reserva sem duplicar
(sem rede real: o servidor roda em 127.0.0.1 e o envio é simulado)."""

from __future__ import annotations

import datetime as dt
import http.server
import json
import threading
import urllib.request

import pytest

from travas.alerts import service as service_mod
from travas.alerts.channels import build_email, parse_contacts
from travas.alerts.server import AlertStore, fingerprint, make_handler
from travas.alerts.service import StopAlerts, armed_positions
from travas.alerts.stop_watch import SentLog, message, triggered, watch_entry
from travas.settings import AlertSettings

TODAY = dt.date.today()
TOKEN = "123456789:" + "A" * 35


def test_parse_contacts_recognizes_lines_with_or_without_labels():
    c = parse_contacts(f"token: {TOKEN}\nchat_id = 1234567890\nemail: fulano@example.com\n")
    assert (c.bot_token, c.chat_id, c.email) == (TOKEN, "1234567890", "fulano@example.com")
    c = parse_contacts(f"{TOKEN}\n-1001234567\n")
    assert c.chat_id == "-1001234567" and c.email is None and c.telegram_ready
    assert b"Subject: Teste" in build_email("a@b.com", "Teste", "corpo")


def _evaluated(down=True, today_price=28.5, pid="abc"):
    tomorrow = TODAY + dt.timedelta(days=1)
    return {
        "id": pid,
        "name": "PETR4 put",
        "kind_label": "Trava de alta com crédito (puts)",
        "underlying": "PETR4",
        "status": "aberta",
        "first_expiration": (TODAY + dt.timedelta(days=30)).isoformat(),
        "max_profit": 60.0,
        "entry_net_per_unit": 0.6,
        "entry_flow": "credito",
        "spot": 31.0,
        "pnl_natural": -55.0,
        "legs": [
            {
                "side": "venda",
                "quantity": 100,
                "symbol": "PETRW300",
                "option_type": "put",
                "strike": 30.0,
            },
            {
                "side": "compra",
                "quantity": 100,
                "symbol": "PETRW280",
                "option_type": "put",
                "strike": 28.0,
            },
        ],
        "stop": {
            "available": True,
            "down": down,
            "pnl_total": -60.0,
            "loss_multiple": 1.0,
            "today_price": today_price,
            "expiry_price": 28.8,
            "by_date": {TODAY.isoformat(): today_price, tomorrow.isoformat(): 28.6},
        },
    }


def test_watch_entry_trigger_and_message():
    entry = watch_entry(_evaluated(), "2026-10-20T10:00:00-03:00")
    assert entry["key"] == "abc:2026-10-20T10:00:00-03:00"
    assert entry["stop_loss_total"] == 60.0
    assert entry["by_date"][entry["expiration"]] == 28.8  # vencimento sempre na tabela
    assert triggered(entry, 29.0, TODAY) is None  # trava de alta: stop abaixo
    assert triggered(entry, 28.4, TODAY) == 28.5
    assert triggered(entry, None, TODAY) is None
    assert triggered(entry, 20.0, TODAY + dt.timedelta(days=5)) is None  # dia sem tabela
    up = watch_entry(_evaluated(down=False, today_price=33.0), "x")
    assert triggered(up, 33.1, TODAY) == 33.0 and triggered(up, 32.0, TODAY) is None
    subject, text = message(entry, 28.4, 28.5, "teste", -55.0)
    assert "PETR4 put" in subject and "28,40" in subject
    assert "R$ 60,00" in text and "Nenhuma ordem" in text and "PETRW300" in text
    closed = {**_evaluated(), "status": "encerrada"}
    assert watch_entry(closed, "x") is None
    assert watch_entry({**_evaluated(), "stop": {"available": False}}, "x") is None


def test_sent_log_reserves_once(tmp_path):
    log = SentLog(tmp_path / "sent.json")
    assert log.add("k", {"by": "app"}) and not log.add("k", {"by": "servidor"})
    log.update("k", {"status": "enviado"})
    assert log.all()["k"] == {"by": "app", "status": "enviado"}
    log.remove("k")
    assert not log.has("k")


@pytest.fixture()
def alert_server(tmp_path):
    store = AlertStore(tmp_path / "srv")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}", store
    server.shutdown()
    server.server_close()


def _call(url, method, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def test_server_routes(alert_server):
    url, store = alert_server
    assert _call(url + "/watch", "PUT", {"entries": [{"key": "a"}]})["watch"] == 1
    creds = {"telegram": {"bot_token": TOKEN, "chat_id": "1"}, "email": None, "google": None}
    pushed = _call(url + "/credentials", "PUT", creds)
    assert pushed["credentials_fingerprint"] == fingerprint(creds)
    status = _call(url + "/status", "GET")
    assert status["watch"] == 1 and status["telegram"] and not status["email"]
    assert TOKEN not in json.dumps(status)  # o token nunca volta pela API
    assert _call(url + "/sent", "POST", {"key": "a", "info": {"by": "app"}})["added"]
    assert not _call(url + "/sent", "POST", {"key": "a", "info": {"by": "x"}})["added"]
    _call(url + "/sent/release", "POST", {"key": "a"})
    assert _call(url + "/sent", "GET")["sent"] == {}


def _alerts(tmp_path, url, records):
    contacts = tmp_path / "telegram-token.txt"
    contacts.write_text(f"{TOKEN}\n1234567890\nfulano@example.com\n", encoding="utf-8")
    cfg = AlertSettings(enabled=True, server_url=url, timeout_seconds=3)
    return StopAlerts(cfg, contacts, tmp_path / "data" / "sent.json", lambda: records)


def test_app_sends_once_and_pushes_watch_list(tmp_path, alert_server, monkeypatch):
    url, store = alert_server
    sent: list[str] = []

    def fake_deliver(contacts, subject, text, gmail):
        sent.append(subject)
        return {"telegram": "ok", "email": "Gmail não autorizado"}

    monkeypatch.setattr(service_mod, "deliver", fake_deliver)
    records = [{"id": "abc", "status": "aberta", "stop_alert": {"enabled": True, "armed_at": "t1"}}]
    alerts = _alerts(tmp_path, url, records)
    ev = {**_evaluated(), "spot": 28.0}  # abaixo do stop de hoje (28,50)
    alerts.process([ev], market_open=False, wait=True)
    assert sent == [] and store.watch.read()["entries"][0]["key"] == "abc:t1"
    assert store.status()["telegram"]  # credenciais enviadas ao servidor
    alerts.process([ev], market_open=True, wait=True)
    alerts.process([ev], market_open=True, wait=True)
    assert len(sent) == 1  # uma vez só
    assert store.sent.all()["abc:t1"]["status"] == "enviado"
    assert alerts.sent_info("abc", "t1")["by"] == "app local"
    # Servidor já reservou outra armação: o app não envia de novo.
    records[0]["stop_alert"]["armed_at"] = "t2"
    store.sent.add("abc:t2", {"by": "servidor", "status": "enviado"})
    alerts.process([ev], market_open=True, wait=True)
    assert len(sent) == 1
    # Desmarcada: some da lista do servidor.
    records[0]["stop_alert"]["enabled"] = False
    alerts.process([], market_open=True, wait=True)
    assert store.watch.read()["entries"] == []


def test_app_sends_even_with_server_down(tmp_path, monkeypatch):
    sent: list[str] = []
    monkeypatch.setattr(service_mod, "deliver", lambda *a: sent.append(a[1]) or {"telegram": "ok"})
    records = [{"id": "abc", "status": "aberta", "stop_alert": {"enabled": True, "armed_at": "t"}}]
    alerts = _alerts(tmp_path, "http://127.0.0.1:9", records)  # porta fechada
    alerts.process([{**_evaluated(), "spot": 28.0}], market_open=True, wait=True)
    assert len(sent) == 1 and "inacessível" in alerts.status()["server_error"]
    assert armed_positions(records) == {"abc": "t"}


def test_server_modules_run_on_debian_python():
    """channels/stop_watch/server rodam no Python 3.13 do Debian, sem as dependências do app."""
    import ast
    from pathlib import Path

    import travas.alerts as pkg

    root = Path(pkg.__file__).parent
    for name in ("__init__.py", "channels.py", "stop_watch.py", "server.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"), feature_version=(3, 13))
        imported = {
            (n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
        } | {
            a.name.split(".")[0]
            for n in ast.walk(tree)
            if isinstance(n, ast.Import)
            for a in n.names
        }
        assert not imported & {"pandas", "numpy", "pydantic", "yaml", "fastapi"}, name
