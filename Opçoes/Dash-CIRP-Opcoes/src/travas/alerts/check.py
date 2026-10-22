"""Checagem do servidor (`travas alerts-check`, a cada 15 min de pregão, no MT5 do Debian).

Lê a lista vigiada enviada pelo app (`watch.json`), a cotação de cada ativo no MT5 e, para cada
estrutura cujo ativo alcançou o stop do dia, reserva o alerta em `sent.json` (o app consulta o
mesmo arquivo pelo servidor HTTP) e envia Telegram + e-mail. Somente leitura no MT5.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
from pathlib import Path

from travas.alerts.channels import deliver, delivered
from travas.alerts.server import AlertStore, contacts_from
from travas.alerts.stop_watch import message, stop_price_on, triggered
from travas.calendar_b3 import B3Calendar
from travas.market_hours import market_status, parse_hhmm
from travas.settings import Settings

log = logging.getLogger(__name__)

CONNECT_SECONDS = 180
STALE_SECONDS = 20 * 60  # tick do ativo mais velho que isto: cotação não confiável
ORIGIN = "servidor Debian (MT5, checagem a cada 15 min de pregão)"


def run_check(settings: Settings, root: Path) -> dict:
    store = AlertStore(root)
    calendar = B3Calendar.from_csv(settings.paths.holidays_file)
    h = settings.market_hours
    market = market_status(
        dt.datetime.now().astimezone(),
        calendar,
        parse_hhmm(h.session_open),
        parse_hhmm(h.session_close),
    )
    today = market.now.date()
    result: dict = {"at": market.now.isoformat(timespec="seconds"), "sent": [], "errors": []}
    entries = store.watch.read()["entries"]
    pending = [
        e for e in entries if not store.sent.has(e["key"]) and stop_price_on(e, today) is not None
    ]
    result["watched"], result["pending"] = len(entries), len(pending)
    if not market.is_open:
        result["skipped"] = market.label
    elif pending:
        _check_pending(settings, store, pending, today, result)
    store.check.write(result)
    log.info("alertas: %s", result)
    return result


def _check_pending(settings, store: AlertStore, pending, today, result) -> None:
    from travas.data import market_data
    from travas.data.snapshot_collector import _connect

    contacts, gmail = contacts_from(store.credentials.read())
    client, _ = _connect(settings, time.monotonic() + CONNECT_SECONDS)
    spots: dict[str, float | None] = {}
    try:
        for underlying in sorted({e["underlying"] for e in pending}):
            try:
                q = market_data.underlying_quote(client, underlying, settings.mt5.server_timezone)
            except Exception as exc:  # noqa: BLE001 — um ativo com problema não para os outros
                result["errors"].append(f"{underlying}: {exc}")
                continue
            fresh = q.pc_lag_seconds is not None and q.pc_lag_seconds <= STALE_SECONDS
            spots[underlying] = q.price if fresh else None
            if not fresh:
                result["errors"].append(f"{underlying}: cotação parada ou sem tick")
    finally:
        client.close()
    result["spots"] = spots
    for entry in pending:
        spot = spots.get(entry["underlying"])
        price = triggered(entry, spot, today)
        if price is None:
            continue
        key = entry["key"]
        claim = {"by": "servidor", "at": result["at"], "spot": spot, "stop_price": price}
        if not store.sent.add(key, {**claim, "status": "enviando"}):
            continue  # o app já enviou
        subject, text = message(entry, spot, price, ORIGIN)
        status = deliver(contacts, subject, text, gmail)
        if delivered(status):
            store.sent.update(key, {"status": "enviado", "channels": status})
            result["sent"].append({"key": key, "channels": status})
        else:
            store.sent.remove(key)  # tenta de novo na próxima checagem
            result["errors"].append(f"{entry['name']}: envio falhou ({status})")
