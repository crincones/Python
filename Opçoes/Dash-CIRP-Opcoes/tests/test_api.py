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

    def broker_name(self):
        return "Corretora Teste"

    def underlyings(self):
        return pd.DataFrame(
            {
                "underlying": ["TEST3", "SEMO3", "IBOV11"],
                "listed_series": [44, 900, 500],
                "has_mt5_options": [True, False, True],
                "category": ["Ação", "Ação", "Índice"],
            }
        )

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
            "paths": SETTINGS.paths.model_copy(
                update={
                    "preferences_file": tmp_path / "p.json",
                    "watchlist_file": tmp_path / "fav.json",
                }
            )
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
    assert "Dash CIRP Opções" in r.text
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
    ev = client.post("/api/tracking/evaluate", json={}).json()
    assert ev["totals"]["realized_pnl"] == pytest.approx(120 - 80)
    rep = client.get("/api/tracking/report").json()
    assert rep["stats"]["trades"] == 1 and rep["stats"]["win_rate"] == 1
    assert client.get("/api/tracking/report?start=2026-10-21").json()["stats"]["trades"] == 0
    csv_r = client.get("/api/tracking/export.csv?scope=encerradas")
    assert csv_r.status_code == 200 and "attachment" in csv_r.headers["content-disposition"]
    lines = csv_r.content.decode("utf-8-sig").splitlines()
    assert len(lines) == 2 and lines[1].split(";")[5] == "Encerrada"
    assert len(client.get("/api/tracking/export.csv?detail=pernas").text.splitlines()) == 3
    assert client.get("/api/tracking/export.csv?scope=abertas").text.count("\n") == 1
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


def test_heatmap_routes(client, monkeypatch):
    import numpy as np
    from test_heatmap import bars

    from travas.heatmap import b3_company

    client.service.daily_set = lambda tickers: (
        {
            t: (bars(np.linspace(20, 31, 300)), {"description": t, "session_deals": 50})
            for t in tickers
        },
        {
            "collected_at": "2026-10-15T11:00:00-03:00",
            "market": {"label": "Mercado aberto", "is_open": True},
        },
    )
    profile = {
        "root": "TEST",
        "is_company": True,
        "sector": "Financeiro",
        "trading_name": "TESTE",
        "isins": {"TEST3": "BRTESTACNOR0"},
    }
    monkeypatch.setattr(b3_company.B3Companies, "profile", lambda self, t, c=None: profile)
    monkeypatch.setattr(
        b3_company.B3Companies,
        "events",
        lambda self, t: {
            "available": True,
            "cash": [],
            "stock": [],
            "subscriptions": [],
            "total_shares": 1000.0,
        },
    )
    r = client.get("/api/heatmap")
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert [i["ticker"] for i in items] == ["SEMO3", "TEST3"]  # IBOV11 fora (índice)
    by = {i["ticker"]: i for i in items}
    assert by["TEST3"]["has_mt5_options"] and not by["SEMO3"]["has_mt5_options"]
    only_mt5 = client.get("/api/heatmap?universe=mt5").json()["items"]
    assert [i["ticker"] for i in only_mt5] == ["TEST3"]
    iv = client.get("/api/heatmap/SEMO3/iv").json()
    assert "não disponibiliza" in iv["unavailable"]
    assert by["TEST3"]["sector"] == "Financeiro"
    assert by["TEST3"]["market_cap_approx"] == pytest.approx(31_000)
    d = client.get("/api/heatmap/TEST3").json()
    assert d["profile"]["trading_name"] == "TESTE" and d["events"]["upcoming"] == []
    assert client.get("/api/heatmap/NADA3").status_code == 404


def test_nobre_fraction_validation(client):
    base = {"underlying": "TEST3", "direction": "alta", "flow": "debito", "nobre_filter": True}
    assert (
        client.post("/api/analyze", json={**base, "nobre_max_cost_fraction": 0.5}).status_code
        == 422
    )
    r = client.post("/api/analyze", json={**base, "nobre_max_cost_fraction": 0.3333})
    assert r.status_code == 200, r.text
    assert "1/3" in r.json()["nobre"]["note"]


def test_underlying_without_mt5_options_is_explained(client):
    r = client.post(
        "/api/analyze", json={"underlying": "SEMO3", "direction": "alta", "flow": "debito"}
    )
    assert r.status_code == 422
    assert (
        "Corretora Teste não disponibiliza no MT5 as opções de SEMO3 (900 séries"
        in r.json()["detail"]
    )
    assert client.get("/api/options/SEMO3").status_code == 422


def test_watchlist_routes(client):
    assert client.get("/api/watchlist").json() == {"items": []}
    r = client.put("/api/watchlist/petr4", json={"price": 31.5})
    assert r.status_code == 200 and r.json()["ticker"] == "PETR4"
    assert r.json()["price_at_add"] == 31.5
    client.put("/api/watchlist/SMAL11")
    # Marcar de novo não duplica nem troca o preço de referência.
    client.put("/api/watchlist/PETR4", json={"price": 40})
    items = client.get("/api/watchlist").json()["items"]
    assert [i["ticker"] for i in items] == ["PETR4", "SMAL11"]
    assert items[0]["price_at_add"] == 31.5 and items[1]["price_at_add"] is None
    assert client.put("/api/watchlist/PETR", json={}).status_code == 422
    assert client.put("/api/watchlist/VALE3", json={"price": -1}).status_code == 422
    assert client.delete("/api/watchlist/PETR4").status_code == 200
    assert client.delete("/api/watchlist/PETR4").status_code == 404
    assert [i["ticker"] for i in client.get("/api/watchlist").json()["items"]] == ["SMAL11"]


def test_protected_scan_and_detail(client):
    r = client.post("/api/protected/scan", json={"underlying": "test3"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["underlying"] == "TEST3"
    assert client.service.scopes[-1].option_types == ("call", "put")
    assert body["results"]
    assert all(row["risk_zero"] for row in body["results"])
    first = body["results"][0]
    d = client.get(f"/api/protected/detail/{body['scan_id']}/{first['id']}")
    assert d.status_code == 200, d.text
    detail = d.json()
    assert detail["simulation"]["model_available"]
    assert detail["limit"]["suggested"] is not None
    assert detail["assumptions"]["notes"]
    assert client.get(f"/api/protected/detail/xxx/{first['id']}").status_code == 404


def test_protected_without_mt5_options(client):
    r = client.post("/api/protected/scan", json={"underlying": "SEMO3"})
    assert r.status_code == 422


def test_detail_has_margin_and_exit_data(client):
    r = client.post(
        "/api/analyze", json={"underlying": "TEST3", "direction": "alta", "flow": "credito"}
    )
    body = r.json()
    first = body["results"][0]
    assert first["margin"]["available"]
    assert first["margin"]["estimated"] == pytest.approx(first["max_loss"] - 0.0)
    d = client.get(f"/api/detail/{body['analysis_id']}/{first['id']}").json()
    sim = d["simulation"]
    assert sim["entry_cash"] == pytest.approx(d["net_premium_total"])
    assert sim["exit_spread_cost"] > 0
    p = client.post("/api/protected/scan", json={"underlying": "TEST3"}).json()
    pd_ = client.get(f"/api/protected/detail/{p['scan_id']}/{p['results'][0]['id']}").json()
    assert pd_["simulation"]["entry_cash"] < 0  # montagem a débito (ativo + opções)


def test_simulator_routes(client):
    exp = synthetic_chain(client.service.calendar)["expiration_date"].iloc[0]
    r = client.get(f"/api/simulator/chain/test3?expiration={exp.isoformat()}")
    assert r.status_code == 200, r.text
    rows = r.json()["rows"]
    assert rows and {"call", "put"} == {row["option_type"] for row in rows}
    assert all(row["bid"] is not None for row in rows)
    legs = [
        {"symbol": "TESTC1131", "side": "compra", "quantity": 100},
        {"symbol": "TESTC1133", "side": "venda", "quantity": 100},
        {"kind": "ativo", "side": "compra", "quantity": 100, "price": 31},
    ]
    e = client.post("/api/simulator/evaluate", json={"underlying": "TEST3", "legs": legs})
    assert e.status_code == 200, e.text
    body = e.json()
    assert len(body["legs"]) == 3 and body["simulation"]["dates"]
    assert body["margin"]["available"]
    bad = client.post(
        "/api/simulator/evaluate",
        json={"underlying": "TEST3", "legs": [{"symbol": "NADA", "side": "compra", "quantity": 1}]},
    )
    assert bad.status_code == 422 and "não encontrado" in bad.json()["detail"]
