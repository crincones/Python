"""API com um serviço de dados falso (sem MT5)."""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import SETTINGS, SPOT, synthetic_chain
from fastapi.testclient import TestClient

from travas.api.app import create_app
from travas.data.market_data import UnderlyingQuote
from travas.data.service import MarketDataUnavailable
from travas.tracking.store import TrackingStore


class FakeService:
    def __init__(self, calendar, available=True):
        self.calendar = calendar
        self.available = available
        self.scopes = []

    def market(self):
        import datetime as dt

        from travas.market_hours import market_status

        return market_status(
            dt.datetime(2026, 10, 14, 11, 0), self.calendar, dt.time(10), dt.time(17, 55)
        )

    def connect_in_background(self):
        pass

    def close(self):
        pass

    def status(self):
        return {"phase": "conectado" if self.available else "erro", "error": None}

    def quote(self, underlying):
        if not self.available:
            raise MarketDataUnavailable("MT5 erro: terminal fechado")
        return UnderlyingQuote(underlying, 30.99, 31.0, SPOT, SPOT, pd.Timestamp.now(tz="UTC"), 5)

    def catalog(self):
        c = synthetic_chain(self.calendar)
        return c[
            ["symbol", "underlying", "option_type", "exercise_style", "strike", "expiration_date"]
        ].assign(contract_size=1.0)

    def leg_quotes(self, underlying, symbols):
        c = synthetic_chain(self.calendar)
        return c[c["symbol"].isin(symbols)].reset_index(drop=True)

    def chain(self, underlying, scope, force=False):
        self.scopes.append(scope)
        chain = synthetic_chain(self.calendar)
        chain = chain[chain["option_type"].isin(scope.option_types)]
        return chain, {"collected_at": "2026-10-14T11:00:00-03:00", "realtime_warning": None}


@pytest.fixture
def client(calendar, tmp_path):
    settings = SETTINGS.model_copy(
        update={
            "paths": SETTINGS.paths.model_copy(update={"preferences_file": tmp_path / "p.json"})
        }
    )
    service = FakeService(calendar)
    store = TrackingStore(tmp_path / "acomp.json")
    with TestClient(create_app(settings, service, store)) as c:
        c.service = service
        yield c


def test_analyze_and_detail(client):
    r = client.post(
        "/api/analyze",
        json={"underlying": "test3", "direction": "alta", "flow": "debito", "target_pct": 8},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["underlying"] == "TEST3"
    assert body["target_price"] == pytest.approx(SPOT * 1.08)
    assert body["results"]
    assert client.service.scopes[0].option_types == ("call",)
    first = body["results"][0]
    d = client.get(f"/api/detail/{body['analysis_id']}/{first['id']}")
    assert d.status_code == 200, d.text
    detail = d.json()
    assert detail["simulation"]["model_available"]
    assert detail["limit"]["suggested"] is not None


def test_credit_put_scope(client):
    r = client.post(
        "/api/analyze", json={"underlying": "TEST3", "direction": "alta", "flow": "credito"}
    )
    assert r.status_code == 200
    assert client.service.scopes[-1].option_types == ("put",)
    assert all(row["kind"] == "alta_credito_put" for row in r.json()["results"])


def test_unavailable_returns_503(client):
    client.service.available = False
    r = client.post(
        "/api/analyze", json={"underlying": "TEST3", "direction": "alta", "flow": "debito"}
    )
    assert r.status_code == 503
    assert "terminal fechado" in r.json()["detail"]


def test_invalid_weights(client):
    r = client.post(
        "/api/analyze",
        json={
            "underlying": "TEST3",
            "direction": "alta",
            "flow": "debito",
            "weights": {
                "scenario": 0,
                "reward_risk": 0,
                "pop": 0,
                "liquidity": 0,
                "execution_cost": 0,
            },
        },
    )
    assert r.status_code == 422


def test_preferences_roundtrip(client):
    assert client.get("/api/preferences").json() == {}
    client.put("/api/preferences", json={"underlying": "PETR4", "side": False})
    assert client.get("/api/preferences").json() == {"underlying": "PETR4", "side": False}


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Analisador de Travas" in r.text
    assert client.get("/static/vendor/klinecharts.min.js").status_code == 200


def test_tracking_flow(client):
    opts = client.get("/api/options/TEST3").json()
    calls = [o for o in opts if o["option_type"] == "call" and o["expiration_date"] == "2026-11-13"]
    k30 = next(o["symbol"] for o in calls if o["strike"] == 30)
    k32 = next(o["symbol"] for o in calls if o["strike"] == 32)
    body = {
        "name": "teste",
        "group": "G1",
        "underlying": "TEST3",
        "legs": [
            {"symbol": k30, "side": "compra", "quantity": 100},
            {"symbol": k32, "side": "venda", "quantity": 100},
        ],
        "entry_net": 0.8,
        "entry_flow": "debito",
        "entry_date": "2026-10-14",
    }
    r = client.post("/api/tracking/positions", json=body)
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    ev = client.post("/api/tracking/evaluate", json={}).json()
    assert ev["positions"][0]["max_loss"] == pytest.approx(80)
    assert ev["groups"][0]["group"] == "G1"
    d = client.post(f"/api/tracking/positions/{pid}/detail", json={}).json()
    assert d["simulation"]["available"]
    g = client.post("/api/tracking/groups/G1/detail", json={})
    assert g.status_code == 200, g.text
    bad = {**body, "legs": [{"symbol": "NAOEXISTE1", "side": "compra", "quantity": 100}]}
    assert client.post("/api/tracking/positions", json=bad).status_code == 422
    closed = client.post(
        f"/api/tracking/positions/{pid}/close",
        json={"exit_date": "2026-10-20", "exit_net": 1.2, "exit_flow": "credito"},
    )
    assert closed.json()["status"] == "encerrada"
    assert client.delete(f"/api/tracking/positions/{pid}").status_code == 200
    assert client.get("/api/tracking/positions").json() == []


def test_icon_cache(tmp_path, monkeypatch):
    from travas.data import icons as icons_mod

    png = icons_mod.PNG_SIGNATURE + b"x" * 10
    calls = []

    def fake_download(self, name):
        calls.append(name)
        return png if name == "PETR" else None

    monkeypatch.setattr(icons_mod.IconCache, "_download", fake_download)
    cache = icons_mod.IconCache(tmp_path, "https://x/{name}.png", 1, True)
    assert cache.path("PETR4").read_bytes() == png  # tentou PETR4 e caiu na raiz PETR
    assert calls == ["PETR4", "PETR"]
    assert cache.path("PETR4") is not None and len(calls) == 2  # agora do disco
    assert cache.path("IBOV11") is None
    n = len(calls)
    assert cache.path("IBOV11") is None and len(calls) == n  # ausência lembrada
    assert cache.path("../x") is None  # nome inválido não vira caminho
