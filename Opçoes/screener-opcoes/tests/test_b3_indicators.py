from __future__ import annotations

import datetime as dt
import json
import urllib.error
from pathlib import Path

import pytest

from screener.market_data import b3_indicators as b3
from screener.settings import load_settings

FIXTURE = Path(__file__).parent / "fixtures" / "b3_indicadores_financeiros_20260917.json"
MARKET = load_settings().market


def test_parses_real_double_encoded_response() -> None:
    body = FIXTURE.read_bytes()
    assert isinstance(json.loads(body), str)  # a API devolve JSON dentro de string
    rate = b3.parse_rate(b3.parse_indicators(body), "TAXA CDI CETIP")
    assert rate.annual == pytest.approx(0.1390)
    assert rate.reference_date == "2026-09-16"
    assert rate.source == b3.SOURCE_B3


def test_parses_plain_array_too() -> None:
    body = json.dumps(
        [{"description": "TAXA CDI CETIP", "rate": "10,65", "lastUpdate": "02/01/2026"}]
    )
    assert b3.parse_rate(b3.parse_indicators(body), "TAXA CDI CETIP").annual == pytest.approx(
        0.1065
    )


@pytest.mark.parametrize(
    ("items", "message"),
    [
        (
            [{"description": "TAXA SELIC", "rate": "13,90", "lastUpdate": "16/09/2026"}],
            "não encontrado",
        ),
        ([{"description": "TAXA CDI CETIP", "rate": "", "lastUpdate": "16/09/2026"}], "inválida"),
        (
            [{"description": "TAXA CDI CETIP", "rate": "139,0", "lastUpdate": "16/09/2026"}],
            "plausível",
        ),
    ],
)
def test_rejects_unexpected_content(items: list, message: str) -> None:
    with pytest.raises(b3.B3IndicatorError, match=message):
        b3.parse_rate(items, "TAXA CDI CETIP")


def test_url_uses_compact_base64_payload() -> None:
    url = b3.indicators_url("https://exemplo/GetFinancialIndicators/")
    assert url.endswith("/eyJsYW5ndWFnZSI6InB0LWJyIn0=")


def test_falls_back_to_yaml_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_: object, **__: object) -> None:
        raise urllib.error.URLError("sem rede")

    monkeypatch.setattr(b3.urllib.request, "urlopen", fail)
    rate = b3.resolve_risk_free_rate(
        MARKET.model_copy(update={"risk_free_rate_source": "b3"}), dt.date(2026, 9, 17)
    )
    assert rate.source == b3.SOURCE_YAML
    assert rate.annual == MARKET.risk_free_rate_annual
    assert "sem rede" in rate.note


def test_uses_b3_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return FIXTURE.read_bytes()

    monkeypatch.setattr(b3.urllib.request, "urlopen", lambda *_, **__: FakeResponse())
    rate = b3.resolve_risk_free_rate(
        MARKET.model_copy(update={"risk_free_rate_source": "b3"}), dt.date(2026, 9, 17)
    )
    assert (rate.source, rate.reference_date) == (b3.SOURCE_B3, "2026-09-16")


def test_yaml_source_skips_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        b3.urllib.request, "urlopen", lambda *_, **__: pytest.fail("não deveria acessar a rede")
    )
    rate = b3.resolve_risk_free_rate(
        MARKET.model_copy(update={"risk_free_rate_source": "yaml"}), dt.date(2026, 9, 17)
    )
    assert rate.source == b3.SOURCE_YAML


@pytest.mark.network
def test_live_b3_cdi() -> None:
    rate = b3.fetch_rate(MARKET)
    assert 0.02 < rate.annual < 0.5
