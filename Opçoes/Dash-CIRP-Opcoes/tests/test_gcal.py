"""Google Agenda: eventos desejados, lembretes e reconciliação (sem rede)."""

from __future__ import annotations

import datetime as dt

from conftest import SETTINGS

from travas.settings import CalendarReminder
from travas.tracking.gcal import desired_events, event_key, plan_sync, reminder_minutes
from travas.tracking.store import TrackingStore

CFG = SETTINGS.google_calendar.model_copy(
    update={
        "event_time": "10:15",
        "reminders": [
            CalendarReminder(business_days_before=5, time="10:30"),
            CalendarReminder(business_days_before=1, time="10:30"),
            CalendarReminder(business_days_before=0, time="10:15"),
        ],
    }
)


def _position(pid: str, status: str = "aberta", expirations=("2026-11-19",)) -> dict:
    return {
        "id": pid,
        "name": f"Trava {pid}",
        "underlying": "BBAS3",
        "group": "Novembro",
        "entry_date": "2026-10-16",
        "status": status,
        "legs": [
            {"symbol": f"L{i}", "side": "compra", "quantity": 100, "option_type": "call",
             "strike": 25.54, "expiration": exp}
            for i, exp in enumerate(expirations)
        ],
    }


def test_reminders_count_sessions_before_expiration(calendar):
    # 19/11/2026: D-1 = 18/11 10:30 (23h45 antes); D-5 = 12/11 10:30 (7 dias − 15 min).
    assert reminder_minutes(dt.date(2026, 11, 19), calendar, CFG) == [0, 1425, 10065]


def test_desired_events_only_open_and_one_per_expiration(calendar):
    positions = [
        _position("a"),
        _position("b", status="encerrada"),
        _position("c", expirations=("2026-11-19", "2026-12-18")),
    ]
    events = desired_events(positions, calendar, CFG)
    assert set(events) == {"a|2026-11-19", "c|2026-11-19", "c|2026-12-18"}
    body = events["a|2026-11-19"]
    assert body["summary"] == "Vencimento 19/11 · Trava a (BBAS3)"
    assert body["start"] == {"dateTime": "2026-11-19T10:15:00", "timeZone": "America/Sao_Paulo"}
    assert [r["minutes"] for r in body["reminders"]["overrides"]] == [0, 1425, 10065]
    assert event_key({"id": "x", **body}) == "a|2026-11-19"
    assert "vencimentos diferentes" in events["c|2026-12-18"]["description"]


def _existing(body: dict, event_id: str, fingerprint: str | None = None) -> dict:
    event = {"id": event_id, **body}
    if fingerprint is not None:
        private = {**body["extendedProperties"]["private"], "fingerprint": fingerprint}
        event["extendedProperties"] = {"private": private}
    return event


def test_plan_creates_updates_and_deletes(calendar):
    desired = desired_events([_position("a"), _position("c")], calendar, CFG)
    closed = desired_events([_position("b")], calendar, CFG)["b|2026-11-19"]
    existing = [
        _existing(desired["a|2026-11-19"], "ev-a"),  # igual: nada a fazer
        _existing(desired["a|2026-11-19"], "ev-a2"),  # duplicado: apagar
        _existing(closed, "ev-b"),  # estrutura encerrada/excluída: apagar
        {"id": "pessoal", "summary": "Dentista"},  # evento que não é do Dash: intocado
    ]
    plan = plan_sync(desired, existing)
    assert [b["summary"] for b in plan.create] == ["Vencimento 19/11 · Trava c (BBAS3)"]
    assert plan.update == []
    assert sorted(plan.delete) == ["ev-a2", "ev-b"]
    changed = plan_sync(desired, [_existing(desired["a|2026-11-19"], "ev-a", "antigo")])
    assert [event_id for event_id, _ in changed.update] == ["ev-a"]


def test_store_notifies_changes(tmp_path):
    store = TrackingStore(tmp_path / "acomp.json")
    calls = []
    store.on_change = lambda: calls.append(1)
    record = store.add(_position("x"))
    store.update(record["id"], {"status": "encerrada"})
    store.delete(record["id"])
    assert len(calls) == 3
