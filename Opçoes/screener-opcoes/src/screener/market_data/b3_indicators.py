"""CDI oficial dos Indicadores Financeiros da B3.

Página: b3.com.br → Market data → Mercado de derivativos → Indicadores financeiros. Os valores vêm
de uma API JSON usada pelo iframe da página (payload = base64 de {"language":"pt-br"}). Com
`Accept: application/json` a API devolve o array codificado duas vezes (string contendo JSON).
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import logging
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from screener.settings import MarketSettings

log = logging.getLogger(__name__)

PAYLOAD = {"language": "pt-br"}
SOURCE_B3 = "b3"
SOURCE_YAML = "yaml"
PERCENT = 100


class B3IndicatorError(RuntimeError):
    """Resposta da B3 ausente, inesperada ou sem o indicador procurado."""


@dataclass(frozen=True)
class RiskFreeRate:
    annual: float
    source: str
    reference_date: str | None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def indicators_url(base_url: str) -> str:
    encoded = base64.b64encode(json.dumps(PAYLOAD, separators=(",", ":")).encode()).decode()
    return base_url.rstrip("/") + "/" + encoded


def parse_indicators(body: str | bytes) -> list[dict[str, Any]]:
    data: Any = json.loads(body)
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, list):
        raise B3IndicatorError(f"formato inesperado: {type(data).__name__}")
    return data


def parse_rate(indicators: list[dict[str, Any]], description: str) -> RiskFreeRate:
    """Taxa anual (fração) e data de referência do indicador com essa descrição."""
    matches = [i for i in indicators if str(i.get("description", "")).strip() == description]
    if not matches:
        raise B3IndicatorError(f"indicador '{description}' não encontrado")
    item = matches[0]
    raw = str(item.get("rate") or item.get("value") or "").strip()
    try:
        annual = float(raw.replace(".", "").replace(",", ".")) / PERCENT
    except ValueError as exc:
        raise B3IndicatorError(f"taxa inválida para '{description}': {raw!r}") from exc
    if not 0 < annual < 1:
        raise B3IndicatorError(f"taxa fora da faixa plausível para '{description}': {raw!r}")
    reference = dt.datetime.strptime(str(item["lastUpdate"]), "%d/%m/%Y").date().isoformat()
    return RiskFreeRate(annual=annual, source=SOURCE_B3, reference_date=reference)


def fetch_rate(market: MarketSettings) -> RiskFreeRate:
    request = urllib.request.Request(
        indicators_url(market.b3_indicators_url), headers={"Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=market.b3_timeout_seconds) as response:
        body = response.read()
    return parse_rate(parse_indicators(body), market.b3_cdi_description)


def resolve_risk_free_rate(market: MarketSettings, today: dt.date) -> RiskFreeRate:
    """Taxa usada na coleta: B3 se configurado; em qualquer falha, o valor do YAML (registrado)."""
    fallback = RiskFreeRate(
        annual=market.risk_free_rate_annual, source=SOURCE_YAML, reference_date=None
    )
    if market.risk_free_rate_source == SOURCE_YAML:
        return fallback
    try:
        rate = fetch_rate(market)
    except (OSError, B3IndicatorError, ValueError, KeyError) as exc:
        log.warning(
            "CDI da B3 indisponível (%s); usando o YAML: %.2f%%",
            exc,
            market.risk_free_rate_annual * PERCENT,
        )
        return RiskFreeRate(
            annual=market.risk_free_rate_annual,
            source=SOURCE_YAML,
            reference_date=None,
            note=f"falha ao buscar na B3: {exc}",
        )
    age = (today - dt.date.fromisoformat(rate.reference_date)).days
    if age > market.max_rate_age_days:
        log.warning("CDI da B3 com referência antiga (%s, %d dias)", rate.reference_date, age)
    log.info("CDI da B3: %.2f%% a.a. (ref. %s)", rate.annual * PERCENT, rate.reference_date)
    return rate
