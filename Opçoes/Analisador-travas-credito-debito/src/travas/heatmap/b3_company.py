"""Dados cadastrais e eventos societários das empresas (API pública de empresas listadas da B3).

Endpoints (sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/…, parâmetro =
JSON em base64):
- GetInitialCompanies: busca por código de negociação (raiz) → codeCVM.
- GetDetail: setor/subsetor/segmento, atividade, site, segmento de listagem, tickers ↔ ISIN.
- GetListedSupplementCompany: proventos em dinheiro (dividendos/JCP: data-com, pagamento, valor),
  proventos em ações (desdobramento, grupamento, bonificação), subscrições, quantidade de ações.
Fusões/aquisições NÃO constam dessa API.

Cache em `data/b3/<RAIZ>.json` (cadastro: 30 dias; proventos/eventos: 1 dia). ETFs não são
empresas listadas: ficam com setor "ETFs" quando a busca não encontra a raiz.
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

log = logging.getLogger(__name__)

BASE = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
DETAIL_TTL = 30 * 86_400
SUPPLEMENT_TTL = 86_400
ETF_SECTOR = "ETFs"
UNKNOWN_SECTOR = "Sem classificação"


def _encode(params: dict) -> str:
    return base64.b64encode(json.dumps(params, separators=(",", ":")).encode()).decode()


def _date(text: str | None) -> str | None:
    """dd/mm/aaaa → ISO; datas-sentinela da B3 (31/12/9999, 01/01/1900) viram None."""
    if not text:
        return None
    try:
        d = dt.datetime.strptime(text.strip()[:10], "%d/%m/%Y").date()
    except ValueError:
        return None
    return None if d.year in (1900, 9999) else d.isoformat()


def _num(text: str | None) -> float | None:
    if text in (None, ""):
        return None
    try:
        return float(str(text).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _fix_sector(text: str | None) -> str | None:
    """A API da B3 troca vírgulas por pontos ("Petróleo. Gás e Biocombustíveis")."""
    return text.replace(". ", ", ") if text else text


def _fix_activity(text: str | None) -> str | None:
    """Na descrição, só ". " seguido de minúscula era vírgula ("Pesquisa. lavra. refino")."""
    return re.sub(r"\. (?=[a-zà-ú])", ", ", text) if text else text


class B3Companies:
    def __init__(self, directory: Path, timeout: float = 15.0) -> None:
        self._dir = directory
        self._timeout = timeout
        self._lock = threading.Lock()

    # ---------- HTTP + cache ----------
    def _get(self, method: str, params: dict) -> object:
        url = f"{BASE}/{method}/{_encode(params)}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, str):  # a API às vezes devolve JSON codificado duas vezes
            data = json.loads(data)
        return data

    def _cache_path(self, root: str) -> Path:
        return self._dir / f"{root}.json"

    def _load(self, root: str) -> dict:
        path = self._cache_path(root)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save(self, root: str, data: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._cache_path(root).with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self._cache_path(root))

    # ---------- consultas ----------
    def profile(self, ticker: str, category: str | None = None) -> dict:
        """Cadastro (setor etc.) da raiz do ticker, com cache de 30 dias. `category` (do arquivo
        de instrumentos da B3: Ação, ETF, BDR…) define o setor quando não há cadastro."""
        root = ticker[:4].upper()
        cached = self._load(root)
        if cached.get("detail_at") and time.time() - cached["detail_at"] < DETAIL_TTL:
            return cached
        try:
            found = self._get(
                "GetInitialCompanies",
                {"language": "pt-br", "pageNumber": 1, "pageSize": 100, "company": root},
            )
            match = next(
                (r for r in found.get("results", []) if r.get("issuingCompany") == root), None
            )
            if match is None:
                fallback = {"ETF": ETF_SECTOR, "BDR": "BDRs"}.get(category or "")
                if fallback is None:
                    fallback = ETF_SECTOR if ticker.endswith("11") else UNKNOWN_SECTOR
                data = {"root": root, "is_company": False, "sector": fallback, "category": category}
            else:
                detail = self._get("GetDetail", {"codeCVM": match["codeCVM"], "language": "pt-br"})
                classes = [
                    c.strip()
                    for c in (_fix_sector(detail.get("industryClassification")) or "").split("/")
                ]
                data = {
                    "root": root,
                    "is_company": True,
                    "code_cvm": match["codeCVM"],
                    "company_name": detail.get("companyName"),
                    "trading_name": detail.get("tradingName"),
                    "sector": classes[0] if classes and classes[0] else UNKNOWN_SECTOR,
                    "subsector": classes[1] if len(classes) > 1 else None,
                    "segment": classes[2] if len(classes) > 2 else None,
                    "activity": _fix_activity(detail.get("activity")),
                    "website": detail.get("website"),
                    "listing_segment": detail.get("market"),
                    "isins": {
                        c["code"]: c["isin"]
                        for c in detail.get("otherCodes") or []
                        if c.get("code")
                    },
                }
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
            log.warning("B3: cadastro de %s indisponível: %s", root, exc)
            if cached:
                return {**cached, "stale": True}
            return {"root": root, "is_company": None, "sector": UNKNOWN_SECTOR, "error": str(exc)}
        merged = {**cached, **data, "detail_at": time.time()}
        with self._lock:
            self._save(root, merged)
        return merged

    def events(self, ticker: str) -> dict:
        """Proventos em dinheiro e em ações + quantidade de ações (cache de 1 dia)."""
        prof = self.profile(ticker)
        root = prof["root"]
        if not prof.get("is_company"):
            kind = {"ETF": "ETF", "BDR": "BDR"}.get(prof.get("category") or "", "ETF ou ativo")
            return {"available": False, "reason": f"{kind} sem cadastro de empresa na B3"}
        cached = self._load(root)
        sup = cached.get("supplement")
        if not sup or time.time() - cached.get("supplement_at", 0) >= SUPPLEMENT_TTL:
            try:
                raw = self._get(
                    "GetListedSupplementCompany", {"issuingCompany": root, "language": "pt-br"}
                )
                sup = raw[0] if isinstance(raw, list) and raw else raw
                with self._lock:
                    self._save(
                        root, {**self._load(root), "supplement": sup, "supplement_at": time.time()}
                    )
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                log.warning("B3: proventos de %s indisponíveis: %s", root, exc)
                if not sup:
                    return {"available": False, "reason": f"B3 indisponível: {exc}"}
        isin = (prof.get("isins") or {}).get(ticker.upper())
        return parse_supplement(sup or {}, isin)

    def prefetch(
        self, tickers: list[str], categories: dict[str, str] | None = None, workers: int = 8
    ) -> dict[str, dict]:
        """Cadastro de vários ativos em paralelo (usado para agrupar o heatmap por setor)."""
        cats = categories or {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            profiles = pool.map(lambda t: self.profile(t, cats.get(t)), tickers)
            return dict(zip(tickers, profiles, strict=True))


def parse_supplement(sup: dict, isin: str | None) -> dict:
    """Normaliza os proventos/eventos; com `isin`, fica só a classe do ticker (ON, PN, unit)."""

    def mine(item: dict) -> bool:
        return isin is None or item.get("isinCode") == isin or item.get("assetIssued") == isin

    cash = [
        {
            "type": item.get("label"),
            "ex_date": _date(item.get("lastDatePrior")),  # data-com (último dia com direito)
            "payment_date": _date(item.get("paymentDate")),
            "approved_on": _date(item.get("approvedOn")),
            "value": _num(item.get("rate")),
            "related_to": item.get("relatedTo"),
        }
        for item in sup.get("cashDividends") or []
        if mine(item)
    ]
    stock = [
        {
            "type": item.get("label"),  # DESDOBRAMENTO, GRUPAMENTO, BONIFICACAO…
            "ex_date": _date(item.get("lastDatePrior")),
            "approved_on": _date(item.get("approvedOn")),
            "factor": _num(item.get("factor")),
        }
        for item in sup.get("stockDividends") or []
        if mine(item)
    ]
    subs = [
        {
            "type": item.get("label"),
            "ex_date": _date(item.get("lastDatePrior")),
            "approved_on": _date(item.get("approvedOn")),
            "percentage": _num(item.get("percentage")),
            "price": _num(item.get("priceUnit")),
        }
        for item in sup.get("subscriptions") or []
        if mine(item)
    ]
    key = lambda e: e.get("ex_date") or e.get("approved_on") or ""  # noqa: E731
    return {
        "available": True,
        "cash": sorted(cash, key=key, reverse=True),
        "stock": sorted(stock, key=key, reverse=True),
        "subscriptions": sorted(subs, key=key, reverse=True),
        "total_shares": _num(sup.get("totalNumberShares")),
        "isin": isin,
    }
